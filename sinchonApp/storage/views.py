# apps/storage/views.py
import os
import uuid
import mimetypes
import logging
from fnmatch import fnmatch

import boto3
from botocore.config import Config
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, parsers
from rest_framework.renderers import JSONRenderer
import logging
from .serializers import *

logger = logging.getLogger(__name__)

class PresignView(APIView):
    # 개발 편의: 인증/CSRF/HTML 렌더 비활성
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    renderer_classes = [JSONRenderer]
    parser_classes = [parsers.JSONParser]

    def post(self, request):
        

        ser = PresignRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        scope = ser.validated_data["scope"]
        filename = ser.validated_data.get("filename") or "file"
        mime_type = ser.validated_data.get("mime_type") or "application/octet-stream"

        # 1) scope / mime 검증
        if scope not in settings.AWS_S3_ALLOWED_SCOPES:
            return Response({"detail": "Invalid scope"}, status=status.HTTP_400_BAD_REQUEST)

        if not self._is_mime_allowed(mime_type):
            return Response({"detail": "Unsupported mime_type"}, status=status.HTTP_400_BAD_REQUEST)

        # 2) 키 생성 (prefix + uuid + 확장자)
        key = self._build_object_key(scope, filename, mime_type)

        # 3) boto3 클라이언트 (자격증명 명시 주입 + IMDS 비활성화)
        os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
        cfg = Config(
            region_name=settings.AWS_REGION,
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=3,
            read_timeout=5,
        )
        s3 = boto3.client(
            "s3",
            config=cfg,
            region_name=settings.AWS_REGION,
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),  # 보통은 없음
        )

        # 4) presigned PUT 생성
        try:
            url = s3.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": settings.AWS_S3_BUCKET,
                    "Key": key,
                    "ContentType": mime_type,
                },
                ExpiresIn=settings.AWS_S3_PRESIGN_EXPIRES,
            )
        except Exception as e:
            logger.exception("presign failed: %s", e)
            return Response({"detail": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        out = PresignResponseSerializer({"upload_url": url, "key": key})
        return Response(out.data, status=status.HTTP_200_OK)

    # ---- helpers ----
    @staticmethod
    def _is_mime_allowed(mime: str) -> bool:
        if not mime:
            return False
        for pattern in settings.AWS_S3_ALLOWED_MIME:
            if fnmatch(mime, pattern):   # image/* 와 같은 패턴 허용
                return True
        return False

    @staticmethod
    def _build_object_key(scope: str, filename: str | None, mime_type: str | None) -> str:
        # filename에서 확장자 추출 시도
        ext = None
        if filename and "." in filename and not filename.endswith("."):
            ext = filename.rsplit(".", 1)[-1].lower()

        # 없으면 mime 기반 추정
        if not ext:
            guessed = mimetypes.guess_extension(mime_type or "")
            ext = (guessed.lstrip(".") if guessed else "bin")

        return f"{scope}/{uuid.uuid4()}.{ext}"

class ConfirmView(APIView):
    """
    클라이언트가 S3 PUT 업로드를 마친 뒤, 업로드된 key/메타데이터를 서버에 통지.
    - key의 scope/경로 검증
    - (가능하면) S3 HeadObject로 존재/메타 확인
    - 최종 접근 URL(CDN or 서명 URL or 공개 S3 URL) 반환
    """
    permission_classes = [permissions.IsAuthenticated]   # ✅ 개발용
    authentication_classes = [JWTAuthentication]                   # 개발 중 인증 생략
    renderer_classes = [JSONRenderer]
    parser_classes = [parsers.JSONParser]

    def post(self, request):
        ser = ConfirmRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        scope = ser.validated_data["scope"]
        key = ser.validated_data["key"].strip()
        mime_type = (ser.validated_data.get("mime_type") or "").strip() or None
        size = ser.validated_data.get("size")

        # 1) scope/key 1차 검증
        if scope not in settings.AWS_S3_ALLOWED_SCOPES:
            return Response({"detail": "Invalid scope"}, status=400)
        if not key or not key.startswith(f"{scope}/"):
            return Response({"detail": "Invalid key or scope/key mismatch"}, status=400)
        if ".." in key or key.startswith("/"):
            return Response({"detail": "Invalid key"}, status=400)

        # (선택) mime 화이트리스트
        if mime_type and not any(fnmatch(mime_type, p) for p in settings.AWS_S3_ALLOWED_MIME):
            return Response({"detail": "Unsupported mime_type"}, status=400)

        # 2) S3 HeadObject로 실제 업로드 확인(가능하면)
        os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            config=Config(
                region_name=settings.AWS_REGION,
                retries={"max_attempts": 3, "mode": "standard"},
                connect_timeout=3, read_timeout=5,
            ),
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
        )

        try:
            head = s3.head_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
            # 사이즈 검증(요청에 size가 왔다면)
            if size is not None and head.get("ContentLength") != int(size):
                return Response({"detail": "Size mismatch"}, status=400)
            # MIME 검증(요청에 mime_type이 왔다면)
            if mime_type and head.get("ContentType") != mime_type:
                # 엄격검증: 불일치 시 거절
                return Response({"detail": "MIME mismatch"}, status=400)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in ("404", "NoSuchKey", "NotFound"):
                return Response({"detail": "Object not found"}, status=400)
            # 권한 부족(AccessDenied) 등은 검증을 생략하고 진행할 수도 있지만, 기본은 에러 처리
            logger.warning("head_object failed: %s", code)
            return Response({"detail": "Cannot verify object"}, status=400)
        except Exception as e:
            logger.exception("head_object error: %s", e)
            return Response({"detail": "Internal Server Error"}, status=500)

        # 3) 최종 URL 결정
        if settings.CDN_BASE_URL:
            url = f"{settings.CDN_BASE_URL.rstrip('/')}/{key}"
        elif settings.AWS_S3_RETURN_SIGNED_ON_CONFIRM:
            # 접근 가능한 링크가 필요하지만 버킷이 private일 수 있으므로 presigned GET 반환(개발에 유용)
            try:
                url = s3.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": settings.AWS_S3_BUCKET, "Key": key},
                    ExpiresIn=settings.AWS_S3_GET_PRESIGN_EXPIRES,
                )
            except Exception:
                return Response({"detail": "Failed to create download URL"}, status=500)
        else:
            # 퍼블릭 버킷일 때만 접근 가능
            url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"

        out = ConfirmResponseSerializer({"url": url})
        return Response(out.data, status=201)
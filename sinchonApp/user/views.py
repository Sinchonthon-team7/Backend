from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import SignupSerializer, LoginSerializer, build_token_payload

class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            # 이메일 중복이면 409, 그 외 검증 실패는 400
            if any(getattr(err, "code", None) == "duplicate" for err in sum(serializer.errors.values(), [])):
                return Response({"detail": "이미 존재하는 아이디입니다."}, status=status.HTTP_409_CONFLICT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(build_token_payload(refresh), status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            # 인증 실패 메시지를 401로
            has_auth_error = any(getattr(err, "code", None) == "auth" for err in sum(serializer.errors.values(), []))
            if has_auth_error:
                return Response({"detail": "아이디 또는 비밀번호가 일치하지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(build_token_payload(refresh), status=status.HTTP_200_OK)
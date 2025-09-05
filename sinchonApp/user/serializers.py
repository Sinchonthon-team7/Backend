from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timezone as dt_timezone

User = get_user_model()

def build_token_payload(refresh: RefreshToken):
    access = refresh.access_token

    def iso_z(exp):
        # exp는 epoch seconds (int)
        return datetime.fromtimestamp(int(exp), tz=dt_timezone.utc) \
                       .isoformat().replace("+00:00", "Z")
    return {
        "grant_type": "Bearer",
        "access": {
            "token": str(access),
            "expire_at": iso_z(access["exp"]),
        },
        "refresh": {
            "token": str(refresh),
            "expire_at": iso_z(refresh["exp"]),
        },
    }



class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("이미 존재하는 아이디입니다.", code="duplicate")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"]
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs.get("username"),
            password=attrs.get("password"),
        )
        if not user:
            raise serializers.ValidationError("아이디 또는 비밀번호가 일치하지 않습니다.", code="auth")
        attrs["user"] = user
        return attrs
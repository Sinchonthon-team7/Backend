from rest_framework import serializers

class PresignRequestSerializer(serializers.Serializer):
    scope = serializers.CharField(required=True)
    filename = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    mime_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class PresignResponseSerializer(serializers.Serializer):
    upload_url = serializers.URLField()
    key = serializers.CharField()

class ConfirmRequestSerializer(serializers.Serializer):
    scope = serializers.CharField()
    key = serializers.CharField()
    mime_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    size = serializers.IntegerField(required=False, allow_null=True, min_value=0)

class ConfirmResponseSerializer(serializers.Serializer):
    url = serializers.URLField()
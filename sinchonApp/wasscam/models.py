from django.db import models
from django.conf import settings

# Create your models here.

CATEGORY_MAP = {
    "보이스피싱": ["택배", "계좌이체", "계좌송금", "서울중앙지검", "검사"],
    "종교": ["신천지", "쩐"],
    "사기": ["3자사기"],
    "마약": ["펜타닐", "케타민", "필로폰", "헤로인", "코카인", "뽕", "우유", "고기", "아이스"],
    "기타": [],
}

class Post(models.Model):
    CATEGORY_CHOICES = [(k, k) for k in CATEGORY_MAP.keys()]

    title = models.CharField(max_length=200)
    #author = models.ForeignKey() 유저모델 만들면 추가
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=20)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    thumbnail_url = models.URLField(blank=True, null=True)

    def __str__ (self):
        return self.title


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='was_likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='was_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='was_comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='was_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"

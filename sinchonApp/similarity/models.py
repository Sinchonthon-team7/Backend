from django.db import models

class PhoneCheck(models.Model):
    number = models.CharField(max_length=32, unique=True)  # 정규화된 번호 E.164-ish or 0으로 시작
    spam = models.CharField(max_length=100, blank=True, null=True)         # 보이스피싱/광고 등
    spam_count_raw = models.CharField(max_length=32, blank=True, null=True) # "1000+" 등 원문
    spam_count = models.IntegerField(default=0)                              # 정규화 수치
    registed_date = models.CharField(max_length=32, blank=True, null=True)
    cyber_crime = models.CharField(max_length=255, blank=True, null=True)
    success = models.IntegerField(default=0)  # 0/1/3
    last_checked_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "phone_checks"

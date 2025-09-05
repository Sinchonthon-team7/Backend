# similarity/urls.py
from django.urls import path
from .views import AssessView, PhoneCheckView

urlpatterns = [
    path("assess/", AssessView.as_view(), name="assess"),
    path("phone-check/", PhoneCheckView.as_view(), name="phone-check"),
]

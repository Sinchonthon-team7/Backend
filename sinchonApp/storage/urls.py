from django.urls import path
from .views import *

urlpatterns = [
    path("presign/", PresignView.as_view(), name="presign"),
    path("confirm/", ConfirmView.as_view(), name="confirm"),
]

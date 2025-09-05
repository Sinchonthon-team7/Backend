from django.urls import path
from isscam.views import *

app_name = "isscam"

urlpatterns = [
    path('posts/', PostListCreateAPIView.as_view(), name='post-list-create'),
    path('posts/<int:pk>/', PostUpdateDeleteAPIView.as_view(), name='post-detail'),
    path('posts/<int:pk>/', PostUpdateDeleteAPIView.as_view(), name='post-detail-updatedelete'),

    path('posts/<int:post_id>/like/', LikeToggleAPIView.as_view(), name='post-like'),

    path('posts/<int:post_id>/comments/', CommentListCreateAPIView.as_view(), name='comment-list-create'),
    path('posts/<int:post_id>/comments/<int:comment_id>/', CommentUpdateDeleteAPIView.as_view(), name='comment-detail'),
]
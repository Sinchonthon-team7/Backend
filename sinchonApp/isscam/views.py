from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Post, Like, Comment
from .serializers import PostSerializer, CommentSerializer, LikeSerializer

# Create your views here.
class PostListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    #permission_classes = [permissions.AllowAny]

    def get(self, request):
        posts = Post.objects.all().order_by('-created_at')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PostDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)

        post.views += 1
        post.save(update_fields=['views'])

        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)
            
class PostUpdateDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    #permission_classes = [permissions.AllowAny]
    
    def get_object(self, pk):
        return get_object_or_404(Post, pk=pk)
    
    def get(self, request, pk):
        post = self.get_object(pk)

        post.views += 1
        post.save(update_fields=['views'])

        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        post = self.get_object(pk)
        if post.author != request.user:
            return Response({"detail": "권한 없음"}, status=status.HTTP_403_FORBIDDEN)
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        post = self.get_object(pk)
        if post.author != request.user:
            return Response({"detail": "권한 없음"}, status=status.HTTP_403_FORBIDDEN)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class LikeToggleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    #permission_classes = [permissions.AllowAny]

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            return Response({"liked": False})
        return Response({"liked": True})
    
class CommentListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    #permission_classes = [permissions.AllowAny]

    def get(self, request, post_id):
        comments = Comment.objects.filter(post_id=post_id).order_by('created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request, post_id):
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, post_id=post_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CommentUpdateDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, post_id, comment_id, user):
        post = get_object_or_404(Post, pk=post_id)
        comment = get_object_or_404(Comment, pk=comment_id, post=post)
        if comment.user != user:
            return Response({"detail": "권한 없음"}, status=status.HTTP_403_FORBIDDEN)
        return comment
    
    def patch(self, request, post_id, comment_id):
        comment = self.get_object(post_id, comment_id, request.user)
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, post_id, comment_id):
        comment = self.get_object(post_id, comment_id, request.user)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
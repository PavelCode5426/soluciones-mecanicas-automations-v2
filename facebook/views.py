from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from facebook.models import FacebookPost
from facebook.serializers import FacebookPostSerializer


class FacebookPostListAPIView(ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = FacebookPost.objects.all()
    serializer_class = FacebookPostSerializer

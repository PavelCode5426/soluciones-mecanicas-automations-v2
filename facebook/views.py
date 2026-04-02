from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from facebook.models import FacebookPostCampaign
from facebook.serializers import FacebookPostSerializer


class FacebookPostListAPIView(ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = FacebookPostCampaign.objects.all()
    serializer_class = FacebookPostSerializer

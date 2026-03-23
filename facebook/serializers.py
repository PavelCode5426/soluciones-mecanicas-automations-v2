from rest_framework import serializers

from facebook.models import FacebookGroup, FacebookPost


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacebookGroup
        fields = serializers.ALL_FIELDS


class FacebookPostSerializer(serializers.ModelSerializer):
    file = serializers.ImageField(read_only=True)
    groups = serializers.SerializerMethodField()

    def get_groups(self, obj):
        return GroupSerializer(FacebookGroup.objects.filter(categories__posts=obj).all(), many=True).data

    class Meta:
        model = FacebookPost
        exclude = ['categories']

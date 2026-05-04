from data_fetcher.global_request_context import get_request

from facebook import models, forms


# class WhatsAppAccountFormViewMixins:
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs.setdefault('request', self.request)
#         return kwargs

class FacebookProfileViewMixins:
    def get_queryset(self):
        return models.FacebookProfile.user_objects.all()


class FilterByProfileViewMixins:
    def get_queryset(self):
        return super().get_queryset().filter(profile__created_by=get_request().user)


class CreateOrUpdatePostViewMixins:

    def post(self, request, *args, **kwargs):
        form = forms.FacebookPostCampaignForm(request.POST)
        formset = forms.FacebookFileInlineFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            post = form.save()
            instances = formset.save(commit=False)
            for instance in instances:
                instance.content_object = post
                instance.save()

#
#
# class FacebookHistoryViewMixins:
#     def get_queryset(self):
#         return models.FacebookHistory.objects.filter(profile__created_by=get_request().user).all()
#
#
# class FacebookGroupViewMixins:
#     def get_queryset(self):
#         return models.FacebookGroup.objects.filter(profile__created_by=get_request().user).all()
#
#
# class FacebookDistributionListViewMixins:
#     def get_queryset(self):
#         return models.FacebookDistributionList.objects.filter(profile__created_by=get_request().user).all()
#
#
# class FacebookMessageViewMixins:
#     def get_queryset(self):
#         return models.FacebookPostCampaign.objects.filter(profile__created_by=get_request().user).all()

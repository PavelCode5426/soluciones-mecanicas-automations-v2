from data_fetcher.global_request_context import get_request

from whatsapp import models


# class WhatsAppAccountFormViewMixins:
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs.setdefault('request', self.request)
#         return kwargs

class WhatsAppAccountViewMixins:
    def get_queryset(self):
        return models.WhatsAppAccount.user_objects.all()


class WhatsAppStatusViewMixins:
    def get_queryset(self):
        return models.WhatsAppStatus.objects.filter(account__created_by=get_request().user).all()


class WhatsAppContactViewMixins:
    def get_queryset(self):
        return models.WhatsAppContact.objects.all()


class WhatsAppGroupViewMixins:
    def get_queryset(self):
        return models.WhatsAppGroup.objects.filter(account__created_by=get_request().user).all()


class WhatsAppDistributionListViewMixins:
    def get_queryset(self):
        return models.WhatsAppDistributionList.objects.filter(account__created_by=get_request().user).all()


class WhatsAppMessageViewMixins:
    def get_queryset(self):
        return models.WhatsAppMessage.objects.filter(account__created_by=get_request().user).all()

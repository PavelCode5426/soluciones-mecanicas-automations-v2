from whatsapp import models


# class WhatsAppAccountFormViewMixins:
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs.setdefault('request', self.request)
#         return kwargs


class WhatsAppStatusViewMixins:
    def get_queryset(self):
        return models.WhatsAppStatus.objects.all()


class WhatsAppContactViewMixins:
    def get_queryset(self):
        return models.WhatsAppContact.objects.all()


class WhatsAppGroupViewMixins:
    def get_queryset(self):
        return models.WhatsAppGroup.objects.all()


class WhatsAppAccountViewMixins:
    def get_queryset(self):
        return models.WhatsAppAccount.objects.all()


class WhatsAppDistributionListViewMixins:
    def get_queryset(self):
        return models.WhatsAppDistributionList.objects.all()


class WhatsAppMessageViewMixins:
    def get_queryset(self):
        return models.WhatsAppMessage.objects.all()

class WhatsAppAccountViewMixins:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault('request', self.request)
        return kwargs

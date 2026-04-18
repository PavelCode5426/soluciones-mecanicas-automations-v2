from django_bootstrap5.renderers import FieldRenderer


class ExtraFieldRenderer(FieldRenderer):
    def add_widget_class_attrs(self, widget=None):
        super().add_widget_class_attrs(widget)


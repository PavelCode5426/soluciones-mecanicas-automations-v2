from django.db import models
from django.forms import forms
from django.http import HttpResponseRedirect
from django.views.generic import FormView, UpdateView, DetailView, DeleteView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import FormMixin
from rest_framework.settings import api_settings
from rest_framework.views import APIView


class MultiplePermissionsView(APIView):
    get_permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    post_permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    put_permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    patch_permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    delete_permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        method = self.request.method.lower()
        permission_classes = getattr(
            self, f"{method}_permission_classes", self.permission_classes
        )
        return [permission() for permission in permission_classes]


class PermissionsMeta(models.Model):
    class Meta:
        abstract = True
        default_permissions = []


class ToggleStatusView(DeleteView):
    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.active = not self.object.active
        self.object.save()
        return HttpResponseRedirect(success_url)


class SingleFormView(FormView, DetailView):
    form_class = forms.Form

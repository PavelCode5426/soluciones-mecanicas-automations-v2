from django.urls import path, include
from whatsapp import views

app_name = 'whatsapp'

urlpatterns = [
    path(r'webhook', views.WhatsAppEventsWebhookView.as_view(), name='webhook'),
]

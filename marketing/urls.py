from django.urls import path, include
from marketing import views

app_name = 'marketing'

urlpatterns = [
    path(r'whatsapp-message/', views.WhatsAppMessageWebhookView.as_view(), name='whatsapp-webhook'),
]

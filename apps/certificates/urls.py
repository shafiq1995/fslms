from django.urls import path

from . import views

app_name = "certificates"

urlpatterns = [
    path("verify/", views.verify, name="verify"),
    path("<int:pk>/pdf/", views.certificate_pdf, name="pdf"),
]

from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    # Student submits payment
    path("submit/", views.payment_submit, name="submit"),
    path("submit/<slug:course_slug>/", views.payment_submit, name="submit_for_course"),

    # Success page
    path("success/<int:tx_id>/", views.payment_success, name="success"),

    # Admin payment management
    path("admin/", views.admin_payments_list, name="admin_payments"),
    path("admin/approve/<int:payment_id>/", views.ajax_approve_payment, name="approve_payment"),
    path("admin/reject/<int:payment_id>/", views.ajax_reject_payment, name="reject_payment"),
    path("admin/refund/<int:payment_id>/", views.ajax_refund_payment, name="refund_payment"),

    # Student & instructor dashboards
    path("my/", views.student_payments, name="student_payments"),
    path("instructor/earnings/", views.instructor_earnings, name="instructor_earnings"),

    # Invoice
    path("invoice/<int:payment_id>/", views.payment_invoice, name="payment_invoice"),
    path("invoice/pdf/<int:payment_id>/", views.payment_invoice_pdf, name="payment_invoice_pdf"),
]

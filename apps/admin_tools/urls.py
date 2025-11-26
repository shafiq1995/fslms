from django.urls import path
from . import views

app_name = "admin_tools"

urlpatterns = [
    # Dashboard / auth
    path("", views.admin_dashboard_view, name="dashboard"),
    path("dashboard/", views.admin_dashboard_view, name="dashboard"),
    path("login/", views.admin_login_view, name="adminlogin"),
    path("logout/", views.admin_logout_view, name="adminlogout"),

    # FAQs (managed from dashboard)
    path("faq/add/", views.faq_add, name="faq_add"),
    path("faq/<int:pk>/update/", views.faq_update, name="faq_update"),
    path("faq/<int:pk>/delete/", views.faq_delete, name="faq_delete"),
    path("faq/", views.faq_manage, name="faq_manage"),

    # Users
    path("users/", views.user_management_list, name="user_management_list"),
    path("users/alias/", views.user_management, name="user_management"),  # optional alias
    path("users/ajax/", views.user_management_ajax, name="user_management_ajax"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:user_id>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:user_id>/delete/", views.user_delete, name="user_delete"),
    path("users/<int:user_id>/toggle-status/", views.toggle_user_status, name="toggle_user_status"),
    path("users/<int:user_id>/", views.user_profile, name="user_profile"),

    # Courses & approvals
    path("courses/", views.admin_course_list, name="admin_course_list"),
    path("courses/approval/", views.course_approval, name="course_approval"),
    path("courses/<int:course_id>/approve/", views.approve_course, name="approve_course"),
    path("courses/<int:course_id>/publish/", views.publish_course, name="publish_course"),
    path("courses/<int:course_id>/reject/", views.reject_course, name="reject_course"),
    path("courses/bulk-action/", views.bulk_course_action, name="bulk_course_action"),

    # Payments overview
    path("payments/", views.payments_list, name="payments"),
    # Certificates
    path("certificates/", views.certificate_list, name="certificate_list"),
    # Blogs
    path("blogs/", views.blog_admin_list, name="blog_admin_list"),

    # Instructor applications
    path("instructors/applications/", views.instructor_applications, name="instructor_applications"),
    path("instructors/<int:user_id>/approve/", views.approve_instructor, name="approve_instructor"),
    path("instructors/<int:user_id>/reject/", views.reject_instructor, name="reject_instructor"),

    # Logs
    path("logs/", views.admin_logs, name="admin_logs"),
]

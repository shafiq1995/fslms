from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Registration & role selection
    path("role-select/", views.role_select_view, name="role_select"),
    path("register/send-code/", views.send_email_code, name="send_email_code"),
    path("register/student/", views.student_register, name="register_student"),
    path("register/instructor/", views.instructor_register, name="register_instructor"),
    path("register/admin/", views.admin_register, name="register_admin"),

    # Profiles
    path("profile/", views.profile_view, name="profile"),
    path("profile/redirect/", views.profile_redirect, name="profile_redirect"),
    path("complete-profile/", views.complete_profile, name="complete_profile"),

    # Password reset flow
    # 1️⃣ Request reset form
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url="/accounts/password-reset/done/",
        ),
        name="password_reset",
    ),

    # 2️⃣ “Email sent” page
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),

    # 3️⃣ Link from email → confirm new password
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/accounts/reset/done/",
        ),
        name="password_reset_confirm",
    ),

    # 4️⃣ Success page after password changed
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]

from django.urls import path
from . import views

app_name = "student_tool"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("enroll/<int:course_id>/", views.enroll_course, name="enroll_course"),
    path("<int:course_id>/", views.course_detail, name="course_detail"),
    path("lessons/<int:lesson_id>/complete/", views.mark_lesson_complete, name="mark_lesson_complete"),
    path("certificates/", views.certificates_list, name="certificates_list"),
    path("certificates/<int:pk>/", views.certificate_detail, name="certificate_detail"),
    path("certificates/<int:pk>/download/", views.certificate_download, name="certificate_download"),
]

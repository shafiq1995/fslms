from django.urls import path
from . import views


app_name = 'instructor_tool'

urlpatterns = [
    # Dashboard & Courses
    path("", views.instructor_dashboard, name="dashboard"),
    path("courses/", views.course_list, name="course_list"),
    path("course/<int:course_id>/manage/", views.course_manage, name="course_manage"),
    path("courses/<int:course_id>/progress/", views.course_progress, name="course_progress"),
    path("courses/<int:course_id>/students/", views.course_students, name="course_students"),
    path("courses/<int:course_id>/student/<int:user_id>/", views.course_student_profile, name="course_student_profile"),
    path("students/", views.students_overview, name="students_overview"),
    path("courses/<int:course_id>/certificates/", views.course_certificates, name="course_certificates"),
    path("courses/<int:course_id>/certificates/<int:cert_id>/reissue/", views.reissue_certificate, name="reissue_certificate"),

    # Sections
    path("course/<int:course_id>/section/create/", views.create_section, name="create_section"),
    path("course/<int:course_id>/section/<int:section_id>/manage/", views.section_manage, name="section_manage"),

    # Lessons
    path("section/<int:section_id>/lesson/create/", views.create_lesson, name="create_lesson"),
    path("course/<int:course_id>/lesson/<int:lesson_id>/manage/", views.lesson_manage, name="lesson_manage"),
    path("lesson/<int:lesson_id>/complete/", views.mark_lesson_complete, name="mark_lesson_complete"),
    path("course/<int:course_id>/resubmit/", views.resubmit_course, name="resubmit_course"),

    # Public Instructor List
    path("instructors/", views.instructor_list, name="list"),
    path("instructor/<int:instructor_id>/", views.instructor_detail, name="detail"),




]

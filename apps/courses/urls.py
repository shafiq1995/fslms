from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    # Course list & creation
    path("", views.course_list, name="course_list"),
    path("create/", views.course_create, name="course_create"),
    path("ajax/create-category/", views.create_category_ajax, name="create_category_ajax"),

    # Single course
    path("<int:course_id>/", views.course_detail, name="course_detail"),
    path("<int:course_id>/edit/", views.course_edit, name="course_edit"),
    path("<int:pk>/delete/", views.course_delete, name="course_delete"),

    # Sections
    path("<int:course_id>/sections/", views.section_list, name="section_list"),
    path("<int:course_id>/sections/add/", views.section_create, name="section_create"),
    path(
        "<int:course_id>/sections/<int:section_id>/edit/",
        views.section_edit,
        name="section_edit",
    ),
    path(
        "<int:course_id>/sections/<int:section_id>/move/<str:direction>/",
        views.move_section,
        name="section_move",
    ),
    path(
        "<int:course_id>/sections/<int:section_id>/delete/",
        views.section_delete,
        name="section_delete",
    ),

    # Lessons
    # Create new lesson inside section
    path(
        "sections/<int:section_id>/lessons/create/",
        views.lesson_create,
        name="lesson_create",
    ),
    # View lesson (student/instructor view)
    path("lessons/<int:lesson_id>/", views.lesson_detail, name="lesson_detail"),
    # Edit/delete lesson
    path("lessons/<int:lesson_id>/edit/", views.lesson_edit, name="lesson_edit"),
    path(
        "<int:course_id>/lessons/<int:lesson_id>/delete/",
        views.lesson_delete,
        name="lesson_delete",
    ),
    path(
        "<int:course_id>/lessons/<int:lesson_id>/move/<str:direction>/",
        views.move_lesson,
        name="lesson_move",
    ),

    # Attachments
    path(
        "lessons/<int:lesson_id>/download/",
        views.lesson_download_attachment,
        name="lesson_download_attachment",
    ),
    path(
        "lessons/<int:lesson_id>/attachments/add/",
        views.lesson_add_attachments,
        name="lesson_add_attachments",
    ),
    path(
        "attachments/<int:attachment_id>/delete/",
        views.delete_lesson_attachment,
        name="delete_lesson_attachment",
    ),

    # Progress control (admin/instructor)
    path(
        "lessons/<int:lesson_id>/complete/",
        views.mark_lesson_completed,
        name="mark_lesson_completed",
    ),
    path(
        "lessons/<int:lesson_id>/reopen/",
        views.reopen_lesson,
        name="reopen_lesson",
    ),
]

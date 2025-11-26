from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, Section, Lesson, LessonAttachment, Enrollment, LessonProgress, Category
from .forms import CourseForm, SectionForm, LessonForm, LessonAttachmentForm
from .services import mark_lesson_for_all_enrollments, recalc_course_progress
from django.http import JsonResponse, HttpResponseForbidden, Http404, FileResponse
import os
from django.utils import timezone
from apps.accounts.models import User
from django.db.models import Prefetch
from django.conf import settings
from django.apps import apps
from django.db.models import Q
from django.db import transaction


from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Course, Category

from django.contrib.auth import get_user_model
User = get_user_model()

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json


@csrf_exempt   # If you use fetch with CSRF token, you can remove this
@require_POST
@login_required
def create_category_ajax(request):
    """Handle AJAX request to create a new CourseCategory."""
    try:
        data = json.loads(request.body)
        name = data.get("name")
        description = data.get("description", "")
        slug = data.get("slug") or slugify(name)

        if not name:
            return JsonResponse({"success": False, "error": "Category name is required."})

        if Category.objects.filter(slug=slug).exists():
            return JsonResponse({"success": False, "error": "A category with this name already exists."})

        category = Category.objects.create(
            name=name,
            slug=slug,
            description=description,
            is_active=True
        )

        return JsonResponse({
            "success": True,
            "category": {
                "id": category.id,
                "name": category.name,
                "slug": category.slug
            }
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

def course_list(request):
    # ====== FILTER INPUTS ======
    search_query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    instructor_id = request.GET.get('instructor', '').strip()
    max_price = request.GET.get('price', '').strip()

    # ====== BASE QUERY ======
    courses = (
        Course.objects.filter(status__in=[Course.STATUS_APPROVED, Course.STATUS_PUBLISHED])
        .select_related('instructor', 'category')
        .defer("description")
    )

    # ====== SEARCH FILTER ======
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # ====== CATEGORY FILTER ======
    if category_id:
        courses = courses.filter(category__id=category_id)

    # ====== INSTRUCTOR FILTER ======
    if instructor_id:
        courses = courses.filter(instructor__id=instructor_id)

    # ====== PRICE FILTER ======
    if max_price:
        try:
            courses = courses.filter(price__lte=float(max_price))
        except ValueError:
            pass  # ignore invalid input gracefully

    # ====== SORTING (Optional Future Feature) ======
    sort_by = request.GET.get('sort', '')
    if sort_by == 'newest':
        courses = courses.order_by('-created_at')
    elif sort_by == 'price_low':
        courses = courses.order_by('price')
    elif sort_by == 'price_high':
        courses = courses.order_by('-price')

    # ====== PAGINATION ======
    paginator = Paginator(courses, 9)  # Show 9 courses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # ====== CONTEXT DATA ======
    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'instructors': User.objects.filter(role="instructor", is_active=True).distinct(),
        'search_query': search_query,
        'selected_category': category_id,
        'selected_instructor': instructor_id,
        'max_price': max_price,
        'sort_by': sort_by,
    }

    return render(request, 'courses/course_list.html', context)



# -------------------------------
# COURSE DETAIL VIEW
# -------------------------------
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

def course_detail(request, course_id):
    """
    Course detail page:
    - Guests can view overview and preview lessons.
    - Enrolled students (or admins/instructors) can view all lessons and download attachments.
    - Instructor/admin get edit/add controls.
    """
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    is_authenticated = user.is_authenticated
    role = getattr(user, "role", None)
    is_admin_or_instructor = (
        is_authenticated
        and (role in ("admin", "instructor") or getattr(user, "is_staff", False))
    )

    # Restrict visibility for non-staff to published/approved courses
    if course.status not in [Course.STATUS_APPROVED, Course.STATUS_PUBLISHED] and not is_admin_or_instructor:
        # allow owner instructor to view their own draft/rejected
        if not (is_authenticated and user == course.instructor):
            raise Http404("Course not available")

    # Prefetch sections + ordered lessons
    sections = course.sections.prefetch_related(
        Prefetch("lessons", queryset=Lesson.objects.order_by("order"))
    ).all()

    # Enrollment via canonical courses.Enrollment model
    enrollment = None
    enrolled = False
    if is_authenticated:
        enrollment = Enrollment.objects.filter(
            user=user,
            course=course,
        ).first()
        enrolled = enrollment is not None

    # Lesson progress: map lesson_id -> bool
    lesson_progress_map = {}
    if enrollment:
        lps = LessonProgress.objects.filter(enrollment=enrollment)
        lesson_progress_map = {lp.lesson_id: lp.is_completed for lp in lps}

    # Total learners for this course
    total_students = Enrollment.objects.filter(course=course).count()

    context = {
        "course": course,
        "sections": sections,
        "enrolled": enrolled,
        "enrollment": enrollment,
        "is_admin_or_instructor": is_admin_or_instructor,
        "lesson_progress_map": lesson_progress_map,
        "total_students": total_students,
    }
    return render(request, "courses/course_detail.html", context)



@login_required
def course_create(request):
    """Allow instructors and admins to create new courses."""
    user = request.user
    role = getattr(user, "role", None)

    # Only instructors/admins/staff may create courses
    if role not in ["instructor", "admin"] and not getattr(user, "is_staff", False):
        messages.error(request, "Only instructors or admins can create courses.")
        return redirect("courses:course_list")

    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            # whoever creates the course becomes the instructor-owner
            course.instructor = user

            # Status rules:
            # - admin/staff: auto-approved
            # - instructor: pending approval
            if role == "admin" or getattr(user, "is_staff", False):
                course.status = Course.STATUS_APPROVED
            else:
                course.status = Course.STATUS_PENDING

            course.save()
            messages.success(
                request,
                "✅ Course created and approved."
                if (role == "admin" or getattr(user, "is_staff", False))
                else "✅ Course submitted for approval."
            )
            return redirect("courses:course_list")
    else:
        form = CourseForm()

    return render(request, "courses/course_create.html", {"form": form})


@login_required
def course_delete(request, pk):
    """Allow instructor or admin to delete a course."""
    course = get_object_or_404(Course, pk=pk)

    # Permission check
    if request.user.role not in ["admin", "instructor"]:
        messages.error(request, "You do not have permission to delete courses.")
        return redirect("courses:course_list")

    if request.user.role == "instructor" and course.instructor != request.user:
        messages.error(request, "You can only delete your own courses.")
        return redirect("courses:course_list")

    if request.method == "POST":
        course_title = course.title
        course.delete()
        messages.success(request, f"Course '{course_title}' deleted successfully.")
        return redirect("courses:course_list")

    # If not confirmed yet
    return render(request, "courses/course_confirm_delete.html", {"course": course})

@login_required
def course_edit(request, course_id):
    """Allow admin to edit any course, instructor only their own."""
    course = get_object_or_404(Course, id=course_id)

    # ✅ Role-based permission check
    if not (request.user.is_staff or request.user == course.instructor):
        messages.error(request, "You do not have permission to edit this course.")
        return redirect('home')

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            updated_course = form.save(commit=False)

            # Instructors cannot self-approve; resubmit draft/rejected to pending
            if not request.user.is_staff and request.user.role != "admin":
                if updated_course.status in [Course.STATUS_DRAFT, Course.STATUS_REJECTED]:
                    updated_course.status = Course.STATUS_PENDING
                    updated_course.status_note = "Resubmitted after edit"

            updated_course.save()
            messages.success(request, f"Course '{updated_course.title}' updated successfully.")
            return redirect('courses:course_detail', course_id=course.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CourseForm(instance=course)

    return render(request, 'courses/course_edit.html', {
        'form': form,
        'course': course,
        'can_edit_status': request.user.is_staff or getattr(request.user, "role", "") == "admin",
    })


@login_required
def section_list(request, course_id):
    """List all sections of a given course."""
    course = get_object_or_404(Course, id=course_id)

    # Permission check
    if request.user.role not in ["admin", "instructor"]:
        messages.error(request, "You do not have permission to view sections.")
        return redirect("courses:course_list")

    if request.user.role == "instructor" and course.instructor != request.user:
        messages.error(request, "You can only manage your own course sections.")
        return redirect("courses:course_list")

    sections = Section.objects.filter(course=course).order_by("order")
    return render(request, "courses/section_list.html", {"course": course, "sections": sections})


@login_required
def section_create(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Same permission rules as section_edit/section_delete
    if request.user.role not in ["admin", "instructor"]:
        messages.error(request, "You do not have permission to add sections.")
        return redirect("courses:course_list")

    if request.user.role == "instructor" and course.instructor != request.user:
        messages.error(request, "You can only add sections to your own courses.")
        return redirect("courses:course_list")

    if request.method == "POST":
        form = SectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.course = course

            # Always assign next order value
            last_section = course.sections.order_by("-order").first()
            section.order = (last_section.order + 1) if last_section and last_section.order else 1

            try:
                section.save()
                messages.success(request, "Section added successfully!")
                return redirect("courses:course_detail", course_id=course.id)
            except Exception as e:
                messages.error(request, f"Error creating section: {e}")
    else:
        form = SectionForm()

    return render(request, "courses/section_create.html", {"form": form, "course": course})


@login_required
def move_section(request, course_id, section_id, direction):
    course = get_object_or_404(Course, id=course_id)
    section = get_object_or_404(Section, id=section_id, course=course)

    if not (request.user.is_staff or request.user == course.instructor):
        return HttpResponseForbidden("You don't have permission to reorder sections.")

    delta = -1 if direction == "up" else 1
    target_order = section.order + delta

    try:
        with transaction.atomic():
            target = Section.objects.select_for_update().get(course=course, order=target_order)
            section.order, target.order = target.order, section.order
            section.save(update_fields=["order"])
            target.save(update_fields=["order"])
    except Section.DoesNotExist:
        pass

    return redirect("instructor_tool:course_manage", course_id=course.id)




@login_required
def section_edit(request, course_id, section_id):
    """Edit an existing section."""
    course = get_object_or_404(Course, id=course_id)
    section = get_object_or_404(Section, id=section_id, course=course)

    if request.user.role not in ["admin", "instructor"]:
        messages.error(request, "You do not have permission to edit sections.")
        return redirect("courses:course_list")

    if request.user.role == "instructor" and course.instructor != request.user:
        messages.error(request, "You can only edit your own course sections.")
        return redirect("courses:course_list")

    if request.method == "POST":
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, f"Section '{section.title}' updated successfully.")
            return redirect("courses:section_list", course_id=course.id)
    else:
        form = SectionForm(instance=section)

    return render(request, "courses/section_form.html", {"form": form, "course": course, "section": section})


@login_required
def section_delete(request, course_id, section_id):
    """Delete a section."""
    course = get_object_or_404(Course, id=course_id)
    section = get_object_or_404(Section, id=section_id, course=course)

    if request.user.role not in ["admin", "instructor"]:
        messages.error(request, "You do not have permission to delete sections.")
        return redirect("courses:course_list")

    if request.user.role == "instructor" and course.instructor != request.user:
        messages.error(request, "You can only delete sections from your own courses.")
        return redirect("courses:course_list")

    if request.method == "POST":
        section_title = section.title
        section.delete()
        messages.success(request, f"Section '{section_title}' deleted successfully.")
        return redirect("courses:section_list", course_id=course.id)

    return render(request, "courses/section_confirm_delete.html", {"course": course, "section": section})

@login_required
def lesson_create(request, section_id):
    """Allow admin/instructor to add a lesson under a specific section."""
    section = get_object_or_404(Section, id=section_id)
    course = section.course

    # Permission check
    if not (request.user.is_staff or request.user == course.instructor):
        messages.error(request, "You don’t have permission to add lessons to this section.")
        return redirect('courses:course_detail', course_id=course.id)

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.section = section
            last = section.lessons.order_by("-order").first()
            lesson.order = (last.order + 1) if last else 1
            lesson.save()
            messages.success(request, f"Lesson '{lesson.title}' added successfully.")
            return redirect('courses:course_detail', course_id=course.id)
    else:
        form = LessonForm()

    return render(request, 'courses/lesson_create.html', {
        'form': form,
        'section': section,
        'course': course,
    })



@login_required
def lesson_edit(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.section.course

    if not (request.user.is_staff or request.user == course.instructor):
        return HttpResponseForbidden("You don’t have permission to edit this lesson.")

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            updated = form.save()
            # recompute progress after commit
            def _recalc():
                try:
                    recalc_course_progress(updated.section.course, issued_by=request.user)
                except Exception:
                    pass
            transaction.on_commit(_recalc)
            messages.success(request, 'Lesson updated successfully.')
            return redirect('courses:course_detail', course_id=course.id)
    else:
        form = LessonForm(instance=lesson)

    return render(request, 'courses/lesson_form.html', {
        'form': form,
        'lesson': lesson,
        'course': course,
    })



@login_required
def lesson_delete(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id)
    lesson = get_object_or_404(Lesson, id=lesson_id, section__course=course)

    if not (request.user.is_staff or request.user == course.instructor):
        return HttpResponseForbidden("You don’t have permission to delete this lesson.")

    if request.method == "POST":
        def _recalc():
            try:
                recalc_course_progress(course, issued_by=request.user)
            except Exception:
                pass

        lesson.delete()
        messages.success(request, f"Lesson '{lesson.title}' deleted successfully.")
        transaction.on_commit(_recalc)
        return redirect("instructor_tool:course_manage", course_id=course.id)

    return redirect("instructor_tool:course_manage", course_id=course.id)



@login_required
def move_lesson(request, course_id, lesson_id, direction):
    course = get_object_or_404(Course, id=course_id)
    lesson = get_object_or_404(Lesson, id=lesson_id, section__course=course)

    if not (request.user.is_staff or request.user == course.instructor):
        return HttpResponseForbidden("You don’t have permission to reorder lessons.")

    delta = -1 if direction == "up" else 1
    target_order = lesson.order + delta
    try:
        with transaction.atomic():
            target = Lesson.objects.select_for_update().get(section=lesson.section, order=target_order)
            lesson.order, target.order = target.order, lesson.order
            lesson.save(update_fields=["order"])
            target.save(update_fields=["order"])
    except Lesson.DoesNotExist:
        pass

    return redirect("instructor_tool:course_manage", course_id=course.id)



def lesson_detail(request, lesson_id):
    """
    Lesson detail view:
      - If user enrolled OR is_admin_or_instructor -> full access
      - If lesson.is_preview -> show preview (limited: hides attachments)
      - Else -> show locked message
    """
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    course = lesson.section.course

    user = request.user
    is_authenticated = user.is_authenticated
    role = getattr(user, "role", None)
    is_admin_or_instructor = (
        is_authenticated
        and (role in ("admin", "instructor") or getattr(user, "is_staff", False))
    )

    # Enrollment via canonical courses.Enrollment model
    enrolled = False
    enrollment = None
    if is_authenticated:
        enrollment = Enrollment.objects.filter(
            user=user,
            course=course,
        ).first()
        enrolled = enrollment is not None

    # allowed to view full lesson?
    can_view_full = (
        is_admin_or_instructor
        or enrolled
        or getattr(lesson, "is_preview", False)
    )

    if not can_view_full:
        return HttpResponseForbidden("You must be enrolled to view this lesson.")

    # Attachments availability (block for preview viewers who are not enrolled/admin/instructor)
    can_view_attachments = is_admin_or_instructor or enrolled

    # Per-user lesson progress
    lesson_completed = False
    if enrollment:
        lp = LessonProgress.objects.filter(
            enrollment=enrollment,
            lesson=lesson,
        ).first()
        if lp:
            lesson_completed = lp.is_completed

    context = {
        "lesson": lesson,
        "course": course,
        "can_view_full": can_view_full,
        "can_view_attachments": can_view_attachments,
        "lesson_completed": lesson_completed,
        "is_admin_or_instructor": is_admin_or_instructor,
        "enrolled": enrolled,
    }
    return render(request, "courses/lesson_detail.html", context)



@login_required
def lesson_download_attachment(request, lesson_id):
    """Allow users to download the lesson attachment."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not lesson.attachment:
        raise Http404("No attachment found for this lesson.")

    course = lesson.section.course
    user = request.user
    is_admin_or_instructor = user.is_authenticated and (
        getattr(user, "is_staff", False) or getattr(user, "role", "") in ("admin", "instructor")
    )
    enrolled = False
    if user.is_authenticated:
        enrolled = Enrollment.objects.filter(user=user, course=course).exists()

    if not (is_admin_or_instructor or enrolled):
        return HttpResponseForbidden("You must be enrolled to download this attachment.")

    file_path = lesson.attachment.path
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
    else:
        raise Http404("File not found.")

@login_required
def lesson_add_attachments(request, lesson_id):
    """Allow admin/instructor to upload multiple attachments to a lesson."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.section.course

    # Permission check
    if not (request.user.is_staff or request.user == course.instructor):
        messages.error(request, "You don't have permission to add attachments.")
        return redirect('courses:lesson_detail', lesson_id=lesson.id)

    if request.method == 'POST':
        files = request.FILES.getlist('file')
        for f in files:
            LessonAttachment.objects.create(
                lesson=lesson,
                file=f,
                title=f.name  # Optional: You could collect titles separately if needed
            )
        messages.success(request, f"{len(files)} file(s) uploaded successfully.")
        return redirect('courses:lesson_detail', lesson_id=lesson.id)

    form = LessonAttachmentForm()
    return render(request, 'courses/lesson_add_attachments.html', {
        'lesson': lesson,
        'form': form,
    })


@login_required
def delete_lesson_attachment(request, attachment_id):
    """AJAX: Allow instructor/admin to delete an attachment."""
    if request.method != "POST":
        return JsonResponse({'error': 'Invalid request method.'}, status=400)

    attachment = get_object_or_404(LessonAttachment, id=attachment_id)
    lesson = attachment.lesson
    course = lesson.section.course

    # Permission check
    if not (request.user.is_staff or request.user == course.instructor):
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    # Delete file safely
    file_name = os.path.basename(attachment.file.name)
    attachment.file.delete(save=False)
    attachment.delete()

    return JsonResponse({'success': True, 'file_name': file_name})



@login_required
def mark_lesson_completed(request, lesson_id):
    """
    Admins/Instructors can mark a lesson as completed.
    This updates the lesson status and recalculates progress for all enrolled students.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.section.course

    # Permission check
    if not (request.user.is_staff or request.user == course.instructor):
        messages.error(request, "You do not have permission to mark this lesson as completed.")
        return redirect('courses:course_detail', course_id=course.id)

    # Mark lesson as completed
    lesson.is_completed = True
    lesson.save(update_fields=["is_completed"])

    # Update all enrolled students’ LessonProgress records
    mark_lesson_for_all_enrollments(lesson, completed=True, marked_by=request.user)

    messages.success(request, f"Lesson '{lesson.title}' marked as completed for all enrolled students.")
    return redirect('courses:course_detail', course_id=course.id)



@login_required
def reopen_lesson(request, lesson_id):
    """
    Allow admin/instructor to unmark a lesson as completed (reopen it).
    Reverts LessonProgress for all enrolled students.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.section.course

    # Permission check
    if not (request.user.is_staff or request.user == course.instructor):
        messages.error(request, "You do not have permission to reopen this lesson.")
        return redirect('courses:course_detail', course_id=course.id)

    # Unmark the lesson
    lesson.is_completed = False
    lesson.save(update_fields=["is_completed"])

    # Revert all LessonProgress records
    mark_lesson_for_all_enrollments(lesson, completed=False, marked_by=request.user)

    messages.info(request, f"Lesson '{lesson.title}' has been reopened for all enrolled students.")
    return redirect('courses:course_detail', course_id=course.id)

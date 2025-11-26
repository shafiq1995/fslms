# src/apps/admin_tools/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

# Import the shared User model and related profiles
from apps.accounts.models import User
from apps.instructor_tool.models import InstructorProfile
from apps.student_tool.models import LearnerProfile
from apps.certificates.models import Certificate

# Courses and payments
from apps.courses.models import Course, Category
from apps.payments.models import Payment  # unified payment model
from apps.blog.models import Post
from apps.faq.models import FAQ

# Admin tools models
from .models import AdminActionLog  # ensure this exists

# Utility
from .utils import log_admin_action  # optional helper you already have; fallback to direct create if absent


def is_admin(user):
    return user.is_authenticated and user.role == "admin"


admin_required = user_passes_test(is_admin, login_url="accounts:login")


# ----------------------------
# Admin auth (login/logout)
# ----------------------------
def admin_login_view(request):
    """
    Dedicated admin login:
    - Only users with role='admin' and is_approved=True can login here.
    """
    if request.user.is_authenticated and is_admin(request.user):
        return redirect("admin_tools:dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_active:
                messages.error(request, "Account is inactive. Contact support.")
                return render(request, "admin_tools/admin_login.html")

            if user.role != "admin":
                messages.error(request, "Not authorized for admin dashboard.")
                return render(request, "admin_tools/admin_login.html")

            # Optional: if you use approval flag on admins
            if not getattr(user, "is_approved", True):
                messages.warning(request, "Admin account is awaiting approval.")
                return render(request, "admin_tools/admin_login.html")

            login(request, user)
            # Log the login action
            log_admin_action(user, "Admin login", user.username)
            return redirect("admin_tools:dashboard")
        else:
            messages.error(request, "Invalid credentials.")

    return render(request, "admin_tools/admin_login.html")



@admin_required
def admin_logout_view(request):
    """Log the admin out and redirect to normal login page."""
    log_admin_action(request.user, "Admin logout", request.user.username)
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("accounts:login")



# ----------------------------
# Dashboard
# ----------------------------
@admin_required
def admin_dashboard_view(request):
    # High-level counts
    total_users = User.objects.count()
    total_students = User.objects.filter(role__in=["student", "learner"]).count()
    total_instructors = User.objects.filter(role="instructor").count()

    # Course status
    active_courses = Course.objects.filter(
        status__in=[Course.STATUS_APPROVED, Course.STATUS_PUBLISHED]
    ).count()
    pending_courses = Course.objects.filter(
        status=Course.STATUS_PENDING
    ).count()

    # Payments summary from canonical Payment model
    pending_payments = Payment.objects.filter(status=Payment.STATUS_PENDING).count()
    total_revenue = (
        Payment.objects.filter(status=Payment.STATUS_COMPLETED)
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    # TODO: wire this if you have a certificates app
    total_certificates = 0

    # Lists for dashboard widgets
    pending_instructors_qs = (
        User.objects.filter(role="instructor", is_approved=False).order_by("-date_joined")
    )
    pending_courses_qs = (
        Course.objects.filter(status=Course.STATUS_PENDING)
        .select_related("instructor", "category")
        .order_by("-created_at")
    )
    pending_payments_qs = (
        Payment.objects.filter(status=Payment.STATUS_PENDING)
        .select_related("user", "course")
        .order_by("-created_at")
    )
    recent_courses = (
        Course.objects.select_related("instructor", "category")
        .order_by("-created_at")[:6]
    )
    recent_payments = (
        Payment.objects.select_related("user", "course")
        .order_by("-created_at")[:8]
    )
    recent_activities = AdminActionLog.objects.select_related("admin").order_by("-created_at")[:10]
    faqs_dashboard = FAQ.objects.filter(is_active=True).order_by("order", "-created_at")[:8]

    from django.core.paginator import Paginator
    pending_instructors = Paginator(pending_instructors_qs, 8).get_page(request.GET.get("instr_page"))
    pending_courses_queue = Paginator(pending_courses_qs, 6).get_page(request.GET.get("course_page"))
    pending_payments_queue = Paginator(pending_payments_qs, 8).get_page(request.GET.get("pay_page"))

    payment_chart_qs = (
        Payment.objects.filter(status=Payment.STATUS_COMPLETED)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum("amount"))
        .order_by("day")
    )
    payment_chart_labels = [p["day"].strftime("%b %d") for p in payment_chart_qs if p["day"]]
    payment_chart_values = [float(p["total"]) for p in payment_chart_qs if p["day"]]

    context = {
        "total_users": total_users,
        "total_students": total_students,
        "total_instructors": total_instructors,
        "active_courses": active_courses,
        "pending_courses": pending_courses,
        "pending_payments": pending_payments,
        "total_revenue": total_revenue,
        "total_certificates": total_certificates,
        "pending_instructors": pending_instructors,
        "pending_courses_queue": pending_courses_queue,
        "pending_payments_queue": pending_payments_queue,
        "recent_courses": recent_courses,
        "recent_payments": recent_payments,
        "recent_activities": recent_activities,
        "payment_chart_labels": payment_chart_labels,
        "payment_chart_values": payment_chart_values,
        "faqs_dashboard": faqs_dashboard,
    }
    return render(request, "admin_tools/admin_dashboard.html", context)


@admin_required
def faq_manage(request):
    """Dedicated FAQ management page (list/add/edit/delete)."""
    faqs = FAQ.objects.all().order_by("order", "-created_at")
    return render(request, "admin_tools/faq_manage.html", {"faqs": faqs})


# ----------------------------
# FAQ management (inline from dashboard)
# ----------------------------
@admin_required
@require_POST
def faq_add(request):
    question = request.POST.get("question", "").strip()
    answer = request.POST.get("answer", "").strip()
    order = request.POST.get("order", "0").strip()
    is_active = bool(request.POST.get("is_active"))
    if question and answer:
        FAQ.objects.create(
            question=question,
            answer=answer,
            order=int(order or 0),
            is_active=is_active,
        )
        messages.success(request, "FAQ added.")
    else:
        messages.error(request, "Question and answer are required.")
    return redirect("admin_tools:dashboard")


@admin_required
@require_POST
def faq_update(request, pk):
    faq = get_object_or_404(FAQ, pk=pk)
    faq.question = request.POST.get("question", faq.question).strip()
    faq.answer = request.POST.get("answer", faq.answer).strip()
    faq.order = int(request.POST.get("order", faq.order) or 0)
    faq.is_active = bool(request.POST.get("is_active"))
    faq.save()
    messages.success(request, "FAQ updated.")
    return redirect("admin_tools:dashboard")


@admin_required
@require_POST
def faq_delete(request, pk):
    faq = get_object_or_404(FAQ, pk=pk)
    faq.delete()
    messages.success(request, "FAQ deleted.")
    return redirect("admin_tools:dashboard")



# ----------------------------
# User Management (list & AJAX partial)
# ----------------------------
@admin_required
def user_management_list(request):
    q = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    status = request.GET.get("status", "").strip()

    qs = User.objects.all().order_by("-date_joined")

    if q:
        qs = qs.filter(username__icontains=q) | qs.filter(email__icontains=q)
    if role:
        qs = qs.filter(role=role)
    if status:
        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "inactive":
            qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 20)
    page = request.GET.get("page", 1)
    users_page = paginator.get_page(page)

    context = {
        "users": users_page,
        "q": q,
        "role": role,
        "status": status,
    }
    return render(request, "admin_tools/user_management_list.html", context)



# alias or older route in urls - keep for compatibility
@admin_required
def user_management(request):
    return user_management_list(request)


# simple AJAX endpoint that returns the table partial (if you prefer)
@admin_required
def user_management_ajax(request):
    if request.method != "GET":
        return HttpResponseBadRequest("GET required.")

    q = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    status = request.GET.get("status", "").strip()

    qs = User.objects.all().order_by("-date_joined")
    if q:
        qs = qs.filter(username__icontains=q) | qs.filter(email__icontains=q)
    if role:
        qs = qs.filter(role=role)
    if status:
        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "inactive":
            qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 20)
    page = request.GET.get("page", 1)
    users_page = paginator.get_page(page)

    return render(request, "admin_tools/user_table_partial.html", {"users": users_page})



# ----------------------------
# Create / Edit / Delete / Toggle
# ----------------------------
@admin_required
def user_create(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email", "")
        password = request.POST.get("password")
        role = request.POST.get("role", "student")

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect("admin_tools:user_management_list")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("admin_tools:user_management_list")

        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = role
        user.is_active = True
        user.is_approved = True if role in ["student", "learner"] else False
        user.save()

        # Create profile based on role
        if role == "instructor":
            InstructorProfile.objects.get_or_create(user=user)
        elif role in ["student", "learner"]:
            LearnerProfile.objects.get_or_create(user=user)

        # Log action
        try:
            log_admin_action(
                request.user,
                "Created user",
                user.username,
                details=f"Role={role}, email={user.email}",
            )

        except Exception:
            pass

        messages.success(request, f"{role.title()} user '{username}' created successfully.")
        return redirect("admin_tools:user_management_list")

    # If GET request → render the user creation form
    return render(request, "admin_tools/user_create.html")


@admin_required
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        username = request.POST.get("username", user.username).strip()
        email = request.POST.get("email", user.email or "")
        role = request.POST.get("role", user.role)
        is_active = bool(request.POST.get("is_active"))

        user.username = username
        user.email = email
        user.role = role
        user.is_active = is_active
        # do not auto-change approval here unless admin toggles it separately
        user.save()

        # ensure profile exists for role
        if role == "instructor":
            InstructorProfile.objects.get_or_create(user=user)
        elif role in ["student", "learner"]:
            LearnerProfile.objects.get_or_create(user=user)

        # log
        log_admin_action(
            request.user,
            "Edited user",
            user.username,
            details="Admin edited user profile from admin panel",
        )

        messages.success(request, "User updated successfully.")
        return redirect("admin_tools:user_management_list")

    return render(request, "admin_tools/user_edit.html", {"user": user})


@admin_required
@require_POST
def user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        return JsonResponse({"success": False, "message": "You cannot delete yourself."}, status=400)
    username = user.username
    user.delete()
    log_admin_action(
        request.user,
        "Deleted user",
        username,
    )

    return JsonResponse({"success": True, "message": f"User {username} deleted."})


@admin_required
@user_passes_test(is_admin)
@require_POST
def toggle_user_status(request, user_id):
    """Toggle user active/inactive status silently and redirect back."""
    user = get_object_or_404(User, id=user_id)

    # Toggle user status
    user.is_active = not user.is_active
    user.save()

    # Log the admin action silently (no messages)
    log_admin_action(
        request.user,
        "Toggled user status",
        user.username,
        details=f"Status changed to {'Active' if user.is_active else 'Inactive'}",
    )

    # Redirect back to user management list
    return redirect(reverse("admin_tools:user_management_list"))


# ----------------------------
# User profile / detail
# ----------------------------
@admin_required
def user_profile(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    instructor_profile = None
    learner_profile = None
    try:
        instructor_profile = InstructorProfile.objects.filter(user=user_obj).first()
    except Exception:
        instructor_profile = None
    try:
        learner_profile = LearnerProfile.objects.filter(user=user_obj).first()
    except Exception:
        learner_profile = None

    # aggregates (example)
    courses_created = Course.objects.filter(instructor=user_obj).count()
    courses_enrolled = 0
    payments = Payment.objects.filter(user=user_obj).order_by("-created_at")[:20]

    context = {
        "user_obj": user_obj,
        "instructor_profile": instructor_profile,
        "learner_profile": learner_profile,
        "courses_created": courses_created,
        "courses_enrolled": courses_enrolled,
        "payments": payments,
    }
    return render(request, "admin_tools/user_profile.html", context)


# ----------------------------
# Instructor applications (pending)
# ----------------------------
@admin_required
def instructor_applications(request):
    pending = User.objects.filter(role="instructor", is_approved=False).order_by("-date_joined")
    context = {"pending_instructors": pending}
    return render(request, "admin_tools/instructor_applications.html", context)


@admin_required
@require_POST
def approve_instructor(request, user_id):
    user = get_object_or_404(User, id=user_id, role="instructor")
    user.is_approved = True
    user.save()
    log_admin_action(request.user, "Approved instructor", user.username)
    messages.success(request, f"Instructor {user.username} approved.")
    return redirect("admin_tools:instructor_applications")


@admin_required
@require_POST
def reject_instructor(request, user_id):
    user = get_object_or_404(User, id=user_id, role="instructor")
    user.is_approved = False
    user.is_active = False
    user.save()
    log_admin_action(request.user, "Rejected instructor", user.username)
    messages.success(request, f"Instructor {user.username} rejected.")
    return redirect("admin_tools:instructor_applications")


# ----------------------------
# Courses: list + approve/reject
# ----------------------------
@admin_required
def admin_course_list(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    qs = (
        Course.objects
        .select_related("instructor", "category")
        .defer("description")
        .prefetch_related("approval_logs")
        .order_by("-created_at")
    )
    if q:
        qs = qs.filter(title__icontains=q)
    if status:
        qs = qs.filter(status__iexact=status)

    paginator = Paginator(qs, 20)
    page = request.GET.get("page", 1)
    courses_page = paginator.get_page(page)

    status_counts = {
        "pending": Course.objects.filter(status=Course.STATUS_PENDING).count(),
        "approved": Course.objects.filter(status=Course.STATUS_APPROVED).count(),
        "published": Course.objects.filter(status=Course.STATUS_PUBLISHED).count(),
        "rejected": Course.objects.filter(status=Course.STATUS_REJECTED).count(),
        "total": Course.objects.count(),
    }

    return render(
        request,
        "admin_tools/admin_course_list.html",
        {
            "courses": courses_page,
            "q": q,
            "status": status,
            "status_counts": status_counts,
        },
    )


@admin_required
def course_approval(request):
    q = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "pending").strip()

    pending_courses = Course.objects.all().select_related("instructor")
    if q:
        pending_courses = pending_courses.filter(title__icontains=q)

    if status_filter == "pending":
        pending_courses = pending_courses.filter(status__in=[Course.STATUS_PENDING])
    elif status_filter == "approved":
        pending_courses = pending_courses.filter(status__in=[Course.STATUS_APPROVED, Course.STATUS_PUBLISHED])
    elif status_filter == "rejected":
        pending_courses = pending_courses.filter(status=Course.STATUS_REJECTED)

    approved_courses = Course.objects.filter(
        status__in=[Course.STATUS_APPROVED, Course.STATUS_PUBLISHED]
    ).order_by("-created_at")[:20]

    context = {
        "pending_courses": pending_courses.order_by("-created_at"),
        "approved_courses": approved_courses,
        "q": q,
        "status_filter": status_filter,
    }
    return render(request, "admin_tools/course_approval.html", context)


@admin_required
def approve_course(request, course_id):
    if request.method != "POST":
        messages.info(request, "Use the approve button to process the course.")
        return redirect("admin_tools:admin_course_list")

    course = get_object_or_404(Course, id=course_id)

    if course.status not in [Course.STATUS_PENDING, Course.STATUS_REJECTED, Course.STATUS_DRAFT]:
        msg = "Only pending/draft/rejected courses can be approved."
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": msg}, status=400)
        messages.error(request, msg)
        return redirect("admin_tools:admin_course_list")

    course.status = Course.STATUS_APPROVED
    course.approved_by = request.user
    course.approved_at = timezone.now()
    course.status_note = ""
    course.save(update_fields=["status", "approved_by", "approved_at", "status_note", "updated_at"])

    log_admin_action(
        request.user,
        "Approved course",
        course.title,
        details=f"Instructor={course.instructor.username}",
    )

    if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
        return JsonResponse({"success": True, "status": course.status})
    messages.success(request, f"Course {course.title} approved.")
    return redirect("admin_tools:admin_course_list")


@admin_required
def publish_course(request, course_id):
    if request.method != "POST":
        messages.info(request, "Use the publish button to process the course.")
        return redirect("admin_tools:admin_course_list")

    course = get_object_or_404(Course, id=course_id)

    if course.status != Course.STATUS_APPROVED:
        msg = "Only approved courses can be published."
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": msg}, status=400)
        messages.error(request, msg)
        return redirect("admin_tools:admin_course_list")

    course.status = Course.STATUS_PUBLISHED
    course.published_at = timezone.now()
    course.save(update_fields=["status", "published_at", "updated_at"])

    log_admin_action(
        request.user,
        "Published course",
        course.title,
        details=f"Instructor={course.instructor.username}",
    )

    if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
        return JsonResponse({"success": True, "status": course.status})
    messages.success(request, f"Course {course.title} published.")
    return redirect("admin_tools:admin_course_list")


@admin_required
def reject_course(request, course_id):
    if request.method != "POST":
        messages.info(request, "Use the reject button to process the course.")
        return redirect("admin_tools:admin_course_list")

    course = get_object_or_404(Course, id=course_id)

    if course.status not in [Course.STATUS_PENDING, Course.STATUS_APPROVED, Course.STATUS_PUBLISHED, Course.STATUS_DRAFT]:
        msg = "Only active courses can be rejected."
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": msg}, status=400)
        messages.error(request, msg)
        return redirect("admin_tools:admin_course_list")

    note = request.POST.get("note", "")
    course.status = Course.STATUS_REJECTED
    course.status_note = note
    course.save(update_fields=["status", "status_note", "updated_at"])

    log_admin_action(
        request.user,
        "Rejected course",
        course.title,
        details=note or "No reason provided",
    )

    if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
        return JsonResponse({"success": True, "status": course.status})
    messages.success(request, f"Course {course.title} rejected.")
    return redirect("admin_tools:admin_course_list")


@admin_required
@require_POST
def bulk_course_action(request):
    """
    Bulk approve/reject/archive with optional note.
    """
    action = request.POST.get("action")
    ids = request.POST.getlist("course_ids")
    note = request.POST.get("note", "")

    if not ids or action not in ["approve", "reject", "archive"]:
        messages.error(request, "Select at least one course and a valid action.")
        return redirect("admin_tools:admin_course_list")

    courses = Course.objects.filter(id__in=ids)
    count = 0
    for course in courses:
        if action == "approve":
            if course.status in [Course.STATUS_PENDING, Course.STATUS_DRAFT, Course.STATUS_REJECTED]:
                course.status = Course.STATUS_APPROVED
                course.approved_by = request.user
                course.approved_at = timezone.now()
                course.status_note = ""
                course.save(update_fields=["status", "approved_by", "approved_at", "status_note", "updated_at"])
                log_admin_action(request.user, "Approved course (bulk)", course.title, details=f"Instructor={course.instructor.username}")
                count += 1
        elif action == "reject":
            if course.status in [Course.STATUS_PENDING, Course.STATUS_APPROVED, Course.STATUS_PUBLISHED, Course.STATUS_DRAFT]:
                course.status = Course.STATUS_REJECTED
                course.status_note = note
                course.save(update_fields=["status", "status_note", "updated_at"])
                log_admin_action(request.user, "Rejected course (bulk)", course.title, details=note or "No reason provided")
                count += 1
        elif action == "archive":
            if course.status not in [Course.STATUS_ARCHIVED]:
                course.status = Course.STATUS_ARCHIVED
                course.save(update_fields=["status", "updated_at"])
                log_admin_action(request.user, "Archived course (bulk)", course.title, details=note or "")
                count += 1

    messages.success(request, f"{count} course(s) processed.")
    return redirect("admin_tools:admin_course_list")


# ----------------------------
# Payments list (overview)
# ----------------------------
@admin_required
def payments_list(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    qs = Payment.objects.all().order_by("-created_at")
    if q:
        qs = qs.filter(user__username__icontains=q) | qs.filter(course__title__icontains=q)
    if status:
        qs = qs.filter(status__iexact=status)

    paginator = Paginator(qs, 25)
    page = request.GET.get("page", 1)
    payments_page = paginator.get_page(page)

    summary = {
        "total": Payment.objects.count(),
        "pending": Payment.objects.filter(status=Payment.STATUS_PENDING).count(),
        "completed": Payment.objects.filter(status=Payment.STATUS_COMPLETED).count(),
        "revenue": Payment.objects.filter(status=Payment.STATUS_COMPLETED).aggregate(total=Sum("amount"))["total"] or 0,
    }

    return render(request, "admin_tools/payments_list.html", {"payments": payments_page, "summary": summary})


# ----------------------------
# Admin logs
# ----------------------------
@admin_required
def admin_logs(request):
    q = request.GET.get("q", "").strip()

    qs = AdminActionLog.objects.all().order_by("-created_at")
    if q:
        from django.db.models import Q

        qs = qs.filter(
            Q(action_type__icontains=q)
            | Q(target_object__icontains=q)
            | Q(admin__username__icontains=q)
        )

    paginator = Paginator(qs, 30)
    page = request.GET.get("page", 1)
    logs_page = paginator.get_page(page)

    context = {
        "page_obj": logs_page,
        "query": q,
    }
    return render(request, "admin_tools/admin_logs.html", context)


@admin_required
def certificate_list(request):
    course_id = request.GET.get("course", "").strip()
    user_id = request.GET.get("user", "").strip()
    qs = Certificate.objects.select_related("course", "user").order_by("-issued_at")
    if course_id:
        qs = qs.filter(course_id=course_id)
    if user_id:
        qs = qs.filter(user_id=user_id)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    courses = Course.objects.only("id", "title")
    users = User.objects.filter(certificates__isnull=False).distinct()

    return render(
        request,
        "admin_tools/certificate_list.html",
        {
            "certificates": page_obj,
            "page_obj": page_obj,
            "courses": courses,
            "users": users,
            "course_id": course_id,
            "user_id": user_id,
        },
    )


@admin_required
def blog_admin_list(request):
    qs = Post.objects.select_related("author").order_by("-created_at")
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "admin_tools/blog_admin_list.html",
        {"posts": page_obj, "page_obj": page_obj},
    )

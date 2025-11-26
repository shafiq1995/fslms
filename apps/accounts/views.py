import random

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    get_user_model,
)
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import NoReverseMatch, reverse

from .forms import (
    StudentRegistrationForm,
    InstructorRegistrationForm,
    AdminRegisterForm,
    UserProfileForm,
    InstructorProfileForm,
    LearnerProfileForm,
)
from .models import UserProfile

User = get_user_model()


def _instructor_profile_completion(user):
    """
    Returns completion percent and missing fields for instructor profiles.
    """
    profile = getattr(user, "profile", None)
    instructor = getattr(user, "instructorprofile", None)

    checks = [
        ("Profile photo", bool(profile and profile.profile_picture) or bool(user.avatar)),
        ("Phone", bool(profile and profile.phone)),
        ("City", bool(profile and profile.city)),
        ("Country", bool(profile and profile.country)),
        ("Bio", bool(profile and profile.bio)),
        ("Professional title", bool(instructor and instructor.professional_title)),
        ("Expertise area", bool(instructor and instructor.expertise_area)),
        ("Skills", bool(instructor and instructor.skills)),
        ("Years of experience", bool(instructor and instructor.experience_years)),
        ("Education", bool(instructor and instructor.education)),
    ]
    completed = [label for label, ok in checks if ok]
    missing = [label for label, ok in checks if not ok]
    percent = round((len(completed) / len(checks)) * 100) if checks else 0
    return {"percent": percent, "missing": missing, "completed": completed}


def login_view(request):
    """
    Handle user login and redirect based on role.
    """
    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password.")
            return render(request, "accounts/Login Page.html")

        if not user.is_active:
            messages.error(
                request,
                "Your account is inactive. Please contact support.",
            )
            return render(request, "accounts/Login Page.html")

        if not user.is_approved:
            messages.warning(
                request,
                "Your account is awaiting admin approval.",
            )
            return render(request, "accounts/pending_approval.html")

        login(request, user)

        if next_url and next_url.startswith("/"):
            return redirect(next_url)

        try:
            if user.is_admin_role() or user.is_superuser:
                return redirect("admin_tools:dashboard")
            elif user.is_instructor():
                return redirect("instructor_tool:dashboard")
            elif user.is_student():
                return redirect("student_tool:dashboard")
            else:
                return redirect("home")
        except NoReverseMatch:
            messages.warning(
                request,
                "Redirect path not set up for your role.",
            )
            return redirect("home")

    return render(request, "accounts/Login Page.html")


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("accounts:login")


def role_select_view(request):
    """
    Allows user to select a role (student or instructor)
    and redirects to the appropriate registration page.
    """
    next_url = request.GET.get("next") or request.POST.get("next")
    if request.method == "POST":
        role = request.POST.get("role")
        if role == "student":
            target = reverse("accounts:register_student")
        elif role == "instructor":
            target = reverse("accounts:register_instructor")
        elif role == "admin":
            target = reverse("accounts:register_admin")
        else:
            return render(
                request,
                "accounts/Role Selection for Registration.html",
                {"error": "Please select a role to continue."},
            )
        if next_url:
            target = f"{target}?next={next_url}"
        return redirect(target)
    return render(request, "accounts/Role Selection for Registration.html", {"next": next_url or ""})


def send_email_code(request):
    """
    AJAX endpoint to send a verification code to the provided email.
    Stores code in session: request.session['email_verification'].
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    email = (request.POST.get("email") or "").strip()
    if not email:
        return JsonResponse({"success": False, "error": "Email is required"}, status=400)

    code = str(random.randint(100000, 999999))
    request.session["email_verification"] = {"email": email, "code": code}
    request.session.modified = True

    try:
        send_mail(
            subject="Your FS LMS verification code",
            message=f"Your verification code is: {code}",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        # We still consider it sent; fail_silently already True
        pass

    return JsonResponse({"success": True, "message": "Verification code sent"})


@login_required
def profile_view(request):
    """
    Display the logged-in user's profile details.
    Works for all user roles.
    """
    user = request.user
    role_label = (
        user.get_role_display() if hasattr(user, "get_role_display") else user.role
    )
    completion = {"percent": 50, "missing": []}
    if user.is_instructor():
        completion = _instructor_profile_completion(user)

    context = {
        "user": user,
        "role": role_label,
        "completion": completion,
    }
    return render(request, "accounts/profile.html", context)


# ==============================
# Student Registration
# ==============================

def student_register(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            code = (request.POST.get("verification_code") or "").strip()
            data = request.session.get("email_verification") or {}
            if not code or data.get("email") != form.cleaned_data.get("email") or data.get("code") != code:
                form.add_error("email", "Please verify your email with the code sent to you.")
                return render(request, "accounts/register_student.html", {"form": form, "next": request.GET.get("next", "")})

            user = form.save(commit=False)
            user.role = User.STUDENT
            user.is_approved = True  # students auto-approved
            user.save()  # signals will create profiles
            messages.success(request, "Student account created successfully.")
            next_url = request.POST.get("next")
            # auto-login then redirect to next if provided
            authed = authenticate(request, username=user.username, password=form.cleaned_data.get("password1"))
            if authed:
                login(request, authed)
                if next_url:
                    return redirect(next_url)
            if next_url:
                return redirect(f"{reverse('accounts:login')}?next={next_url}")
            return redirect("accounts:login")
    else:
        form = StudentRegistrationForm()
    return render(request, "accounts/register_student.html", {"form": form, "next": request.GET.get("next", "")})


# ==============================
# Instructor Registration
# ==============================

def instructor_register(request):
    if request.method == "POST":
        form = InstructorRegistrationForm(request.POST)
        if form.is_valid():
            code = (request.POST.get("verification_code") or "").strip()
            data = request.session.get("email_verification") or {}
            if not code or data.get("email") != form.cleaned_data.get("email") or data.get("code") != code:
                form.add_error("email", "Please verify your email with the code sent to you.")
                return render(request, "accounts/register_instructor.html", {"form": form, "next": request.GET.get("next", "")})

            user = form.save(commit=False)
            user.role = User.INSTRUCTOR
            user.is_approved = False  # require admin approval
            user.save()
            messages.success(
                request,
                "Instructor account created successfully. "
                "Your account is pending admin approval.",
            )
            next_url = request.POST.get("next")
            if next_url:
                return redirect(f"{reverse('accounts:login')}?next={next_url}")
            return redirect("accounts:login")
    else:
        form = InstructorRegistrationForm()
    return render(request, "accounts/register_instructor.html", {"form": form, "next": request.GET.get("next", "")})


# ==============================
# Admin Registration
# ==============================

def admin_register(request):
    if request.method == "POST":
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            code = (request.POST.get("verification_code") or "").strip()
            data = request.session.get("email_verification") or {}
            if not code or data.get("email") != form.cleaned_data.get("email") or data.get("code") != code:
                form.add_error("email", "Please verify your email with the code sent to you.")
                return render(request, "accounts/register_admin.html", {"form": form})

            user = form.save(commit=False)
            user.role = User.ADMIN
            user.is_staff = True
            user.is_superuser = False
            user.is_approved = True
            user.save()
            messages.success(request, "Admin account created successfully!")
            # Allow them to go to Django admin
            return redirect("admin:index")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AdminRegisterForm()

    return render(request, "accounts/register_admin.html", {"form": form})


# ==============================
# Login Redirection Helper
# ==============================

@login_required
def profile_redirect(request):
    """Redirects user based on role."""
    user = request.user
    try:
        if user.is_student():
            return redirect("student_tool:dashboard")
        elif user.is_instructor():
            return redirect("instructor_tool:dashboard")
        elif user.is_admin_role() or user.is_superuser:
            # Prefer custom admin dashboard; fallback to Django admin
            try:
                return redirect("admin_tools:dashboard")
            except NoReverseMatch:
                return redirect("admin:index")
    except Exception:
        pass

    messages.error(request, "Invalid user role.")
    return redirect("accounts:login")


# ==============================
# Complete Profile (role-aware)
# ==============================

@login_required
def complete_profile(request):
    """
    Unified profile completion for all roles.
    - Always shows UserProfileForm
    - Shows extra InstructorProfileForm for instructors
    - Shows extra LearnerProfileForm for students/learners
    - Admins only see the common UserProfileForm
    """
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    role = getattr(user, "role", None)

    # Avoid circular imports by using apps.get_model
    InstructorProfile = apps.get_model("instructor_tool", "InstructorProfile")
    LearnerProfile = apps.get_model("student_tool", "LearnerProfile")

    user_form = UserProfileForm(instance=profile)
    instructor_form = None
    learner_form = None
    form_submitted = False

    if request.method == "POST":
        user_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if user.is_instructor():
            instructor_profile, _ = InstructorProfile.objects.get_or_create(
                user=user
            )
            instructor_form = InstructorProfileForm(
                request.POST,
                request.FILES,
                instance=instructor_profile,
            )
            if user_form.is_valid() and instructor_form.is_valid():
                user_form.save()
                instructor_form.save()
                messages.success(
                    request,
                    "Instructor profile updated successfully.",
                )
                form_submitted = True

        elif user.is_student():
            learner_profile, _ = LearnerProfile.objects.get_or_create(user=user)
            learner_form = LearnerProfileForm(
                request.POST,
                request.FILES,
                instance=learner_profile,
            )
            if user_form.is_valid() and learner_form.is_valid():
                user_form.save()
                learner_form.save()
                messages.success(
                    request,
                    "Profile updated successfully.",
                )
                form_submitted = True

        else:
            # Admin or any other roles – only base profile
            if user_form.is_valid():
                user_form.save()
                messages.success(request, "Profile updated successfully.")
                form_submitted = True

    else:
        if user.is_instructor():
            instructor_profile, _ = InstructorProfile.objects.get_or_create(
                user=user
            )
            instructor_form = InstructorProfileForm(instance=instructor_profile)
        elif user.is_student():
            learner_profile, _ = LearnerProfile.objects.get_or_create(user=user)
            learner_form = LearnerProfileForm(instance=learner_profile)

    context = {
        "user_form": user_form,
        "instructor_form": instructor_form,
        "learner_form": learner_form,
        "role": role,
        "form_submitted": form_submitted,
    }
    return render(request, "accounts/complete_profile.html", context)

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile
from apps.instructor_tool.models import InstructorProfile
from apps.student_tool.models import LearnerProfile

User = get_user_model()


# -----------------------------
#  Registration Forms
# -----------------------------

class StudentRegistrationForm(UserCreationForm):
    """Registration form for students."""
    first_name = forms.CharField(required=True, label="First Name")
    last_name = forms.CharField(required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")
    phone = forms.CharField(required=False, label="Phone Number")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        # role & approval handled in the view
        if commit:
            user.save()
            phone = self.cleaned_data.get("phone")
            if phone:
                from .models import UserProfile
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.phone = phone
                profile.save()
        return user


class InstructorRegistrationForm(UserCreationForm):
    """Registration form for instructors."""
    first_name = forms.CharField(required=True, label="First Name")
    last_name = forms.CharField(required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")
    phone = forms.CharField(required=False, label="Phone Number")
    professional_title = forms.CharField(required=False, label="Professional Title")
    expertise_area = forms.CharField(required=False, label="Expertise Area")
    skills = forms.CharField(required=False, label="Key Skills", help_text="Comma separated")
    experience_years = forms.IntegerField(required=False, min_value=0, label="Years of Experience")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "professional_title",
            "expertise_area",
            "skills",
            "experience_years",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            from .models import UserProfile
            from apps.instructor_tool.models import InstructorProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            phone = self.cleaned_data.get("phone")
            if phone:
                profile.phone = phone
                profile.save()
            instr_prof, _ = InstructorProfile.objects.get_or_create(user=user)
            for field in ["professional_title", "expertise_area", "skills", "experience_years"]:
                val = self.cleaned_data.get(field)
                if val:
                    setattr(instr_prof, field, val)
            instr_prof.save()
        return user


# -----------------------------
#  Profile Edit Forms
# -----------------------------

class UserProfileForm(forms.ModelForm):
    """Form for common user profile data."""
    class Meta:
        model = UserProfile
        fields = [
            "phone",
            "bio",
            "profile_picture",
            "address",
            "date_of_birth",
            "city",
            "country",
            "preferred_language",
            "timezone",
            "gender",
        ]


class InstructorProfileForm(forms.ModelForm):
    """Form for instructor-specific data."""
    class Meta:
        model = InstructorProfile
        fields = [
            "professional_title",
            "education",
            "experience_years",
            "expertise_area",
            "skills",
            "languages",
            "linkedin",
            "twitter",
            "website",
            "cv_resume",
            "id_verification",
            "bank_account",
            "payment_method",
            "signature_image",
        ]


class LearnerProfileForm(forms.ModelForm):
    """Form for learner-specific data."""
    class Meta:
        model = LearnerProfile
        fields = [
            "student_id",
            "education_level",
            "institution_name",
            "learning_goal",
            "preferred_language",
            "interests",
            "resume",
            "special_needs",
            "guardian_name",
            "emergency_contact",
        ]


# -----------------------------
#  Admin Registration Form
# -----------------------------

class AdminRegisterForm(UserCreationForm):
    """
    Form for registering admin users via the frontend.
    Keeps `full_name` and `phone` fields for UI,
    but maps them to User + UserProfile.
    """
    email = forms.EmailField(required=True)
    full_name = forms.CharField(label="Full Name", max_length=100)
    phone = forms.CharField(label="Phone Number", max_length=20, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        full_name = self.cleaned_data.get("full_name", "").strip()
        first_name, last_name = "", ""
        if full_name:
            parts = full_name.split(" ", 1)
            first_name = parts[0]
            if len(parts) > 1:
                last_name = parts[1]

        user.first_name = first_name
        user.last_name = last_name

        # Admin role flags
        user.role = User.ADMIN
        user.is_staff = True
        user.is_superuser = False
        user.is_approved = True

        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            phone = self.cleaned_data.get("phone")
            if phone:
                profile.phone = phone
                profile.save()
        return user

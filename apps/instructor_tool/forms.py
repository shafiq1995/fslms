from django import forms
from apps.student_tool.models import LearnerProfile


class LearnerProfileForm(forms.ModelForm):
    class Meta:
        model = LearnerProfile
        exclude = ['user', 'total_courses_enrolled', 'total_certificates', 'created_at', 'updated_at']
        widgets = {
            'learning_goal': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
from django import forms
from apps.courses.models import Section

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter section title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Optional"}),
        }

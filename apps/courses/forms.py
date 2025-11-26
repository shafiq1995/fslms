from django import forms

from .models import Course, Section, Lesson, LessonAttachment


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class LessonAttachmentForm(forms.ModelForm):
    class Meta:
        model = LessonAttachment
        fields = ["file", "title"]
        widgets = {
            "file": MultiFileInput(attrs={"class": "form-control", "multiple": True}),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional title for attachment",
                }
            ),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "title",
            "content",
            "video",
            "attachment",
            "lesson_type",
            "join_link",
            "scheduled_at",
            "duration_minutes",
            "resource_links",
            "order",
            "is_published",
            "is_preview",
            "is_completed",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "video": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "attachment": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "lesson_type": forms.Select(attrs={"class": "form-select"}),
            "join_link": forms.URLInput(attrs={"class": "form-control"}),
            "scheduled_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "duration_minutes": forms.NumberInput(attrs={"class": "form-control"}),
            "resource_links": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_preview": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_completed": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter section title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional"}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "title",
            "slug",
            "short_description",
            "description",
            "category",
            "language",
            "level",
            "price",
            "discount_price",
            "thumbnail",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "short_description": forms.TextInput(attrs={"class": "form-control", "placeholder": "1–2 sentence summary (required for approval)"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "language": forms.TextInput(attrs={"class": "form-control"}),
            "level": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "discount_price": forms.NumberInput(attrs={"class": "form-control"}),
            "thumbnail": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

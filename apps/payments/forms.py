# apps/payments/forms.py
from django import forms
from .models import Payment


class PaymentNoteForm(forms.Form):
    """Used by admin to leave remarks or comments on payments."""
    note = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        required=False,
        label="Admin Note"
    )


class StudentPaymentForm(forms.ModelForm):
    """Used by students to submit payment TxID for a course."""

    class Meta:
        model = Payment
        fields = ["provider", "provider_tx_id", "amount", "note"]
        widgets = {
            "provider": forms.Select(attrs={"class": "form-select"}),
            "provider_tx_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter TxID"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

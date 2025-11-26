from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.courses.models import Course, Enrollment
from apps.admin_tools.views import is_admin
from .forms import PaymentNoteForm, StudentPaymentForm
from .models import Payment
from .services import approve_payment, reject_payment, refund_payment


def is_staff_or_admin(user):
    return user.is_authenticated and (user.is_staff or getattr(user, "role", "") == "admin")


# ========== Student: Submit Payment ==========
@login_required
def payment_submit(request, course_slug=None):
    """
    Students submit a payment TxID. Enrollment is activated after admin approval.
    """
    if not getattr(request.user, "role", "") in ("student", "learner"):
        messages.error(request, "Only students can submit payments.")
        return redirect("home")

    course = get_object_or_404(Course, slug=course_slug) if course_slug else None
    if course and course.status not in [Course.STATUS_APPROVED, Course.STATUS_PUBLISHED]:
        messages.error(request, "This course is not open for enrollment.")
        return redirect("courses:course_detail", course_id=course.id)

    if request.method == "POST":
        form = StudentPaymentForm(request.POST)
        if form.is_valid():
            provider_tx_id = form.cleaned_data["provider_tx_id"]

            # Prevent duplicate Tx IDs
            if Payment.objects.filter(provider_tx_id=provider_tx_id).exists():
                messages.error(request, "This transaction ID has already been used.")
                return redirect("payments:submit_for_course", course_slug=course.slug)

            # Prevent duplicate pending for same user/course
            if course and Payment.objects.filter(user=request.user, course=course, status=Payment.STATUS_PENDING).exists():
                messages.warning(request, "You already have a pending payment for this course.")
                return redirect("student_tool:dashboard")

            payment = form.save(commit=False)
            payment.user = request.user
            payment.course = course
            # Default amount to course price if not provided
            if not payment.amount and course:
                payment.amount = course.price
            payment.save()

            messages.success(request, "Payment submitted. Waiting for admin approval.")
            return redirect("student_tool:dashboard")
    else:
        initial = {}
        if course:
            initial["amount"] = course.price
        form = StudentPaymentForm(initial=initial)

    return render(request, "student_tool/payment_form.html", {"course": course, "form": form})


# ========== Student: Payment Success ==========
@login_required
def payment_success(request, tx_id):
    payment = get_object_or_404(Payment, id=tx_id)
    if payment.user != request.user and not is_staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")
    return render(request, "payments/payment_success.html", {"payment": payment})


# ========== Admin: View All Payments ==========
@login_required
@user_passes_test(is_staff_or_admin)
def admin_payments_list(request):
    q = request.GET.get("q", "")
    status = request.GET.get("status", "all")
    provider = request.GET.get("provider", "")
    start = request.GET.get("start_date", "")
    end = request.GET.get("end_date", "")

    payments = (
        Payment.objects.select_related("user", "course")
        .order_by("-created_at")
    )

    if q:
        payments = payments.filter(
            Q(user__username__icontains=q)
            | Q(user__email__icontains=q)
            | Q(provider_tx_id__icontains=q)
            | Q(course__title__icontains=q)
        )
    if status and status != "all":
        payments = payments.filter(status=status)
    if provider:
        payments = payments.filter(provider=provider)
    if start:
        payments = payments.filter(created_at__date__gte=start)
    if end:
        payments = payments.filter(created_at__date__lte=end)

    from django.core.paginator import Paginator
    paginator = Paginator(payments, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    total_payments = payments.count()
    pending_count = payments.filter(status=Payment.STATUS_PENDING).count()
    completed_count = payments.filter(status=Payment.STATUS_COMPLETED).count()
    total_revenue = (
        payments.filter(status=Payment.STATUS_COMPLETED).aggregate(Sum("amount"))["amount__sum"] or 0
    )

    context = {
        "payments": page_obj,
        "page_obj": page_obj,
        "total_payments": total_payments,
        "pending_count": pending_count,
        "completed_count": completed_count,
        "total_revenue": total_revenue,
        "filters": {
            "q": q,
            "status": status,
            "provider": provider,
            "start": start,
            "end": end,
        },
    }
    return render(request, "admin_tools/payments_list.html", context)


# ========== Student Payments ==========
@login_required
def student_payments(request):
    payments = Payment.objects.filter(user=request.user).select_related("course").order_by("-created_at")
    return render(request, "payments/student_payments.html", {"payments": payments})


# ========== Instructor Earnings ==========
@login_required
@user_passes_test(lambda u: getattr(u, "role", "") == "instructor" or u.is_staff)
def instructor_earnings(request):
    payments = Payment.objects.filter(course__instructor=request.user, status=Payment.STATUS_COMPLETED)
    total_earnings = sum(p.amount for p in payments)
    return render(
        request,
        "payments/instructor_earnings.html",
        {"payments": payments, "total_earnings": total_earnings},
    )


# ========== AJAX Approvals ==========
from django.views.decorators.http import require_POST


@login_required
@user_passes_test(is_staff_or_admin)
@require_POST
def ajax_approve_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    try:
        approve_payment(payment, admin_user=request.user)
        # If JSON/AJAX expected
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Payment approved and enrollment activated."})
        messages.success(request, f"Payment #{payment.id} approved and enrollment activated.")
    except ValueError as exc:
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": str(exc)}, status=400)
        messages.error(request, str(exc))
    return redirect("admin_tools:dashboard")


@login_required
@user_passes_test(is_staff_or_admin)
@require_POST
def ajax_reject_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    note = request.POST.get("note", "")
    try:
        reject_payment(payment, admin_user=request.user, note=note)
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Payment rejected."})
        messages.info(request, f"Payment #{payment.id} rejected.")
    except ValueError as exc:
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": str(exc)}, status=400)
        messages.error(request, str(exc))
    return redirect("admin_tools:dashboard")


@login_required
@user_passes_test(is_staff_or_admin)
@require_POST
def ajax_refund_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    note = request.POST.get("note", "")
    try:
        refund_payment(payment, admin_user=request.user, note=note)
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Payment marked as refunded."})
        messages.info(request, f"Payment #{payment.id} refunded.")
    except ValueError as exc:
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": str(exc)}, status=400)
        messages.error(request, str(exc))
    return redirect("admin_tools:dashboard")


# ========== Invoice ==========
@login_required
def payment_invoice(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if payment.user != request.user and not is_staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")
    return render(request, "payments/payment_invoice.html", {"payment": payment})


@login_required
@user_passes_test(is_admin)
def payment_invoice_pdf(request, payment_id):
    """
    Render invoice HTML; if html2pdf/xhtml2pdf is installed, return a PDF, else fallback to HTML.
    """
    payment = get_object_or_404(Payment.objects.select_related("user", "course"), id=payment_id)
    template_path = "payments/payment_invoice_pdf.html"
    context = {"payment": payment}

    try:
        from xhtml2pdf import pisa  # type: ignore
    except ImportError:
        # No PDF backend installed; show HTML with a hint
        return render(request, template_path, {**context, "pdf_disabled": True})

    html = get_template(template_path).render(context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Invoice_{payment.id}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response, encoding="UTF-8")
    if pisa_status.err:
        return HttpResponseBadRequest("Error generating PDF invoice.")
    return response

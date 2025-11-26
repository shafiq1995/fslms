from io import BytesIO

from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.template.loader import get_template

from .models import Certificate


def _render_pdf(certificate):
    """
    Render the certificate HTML to PDF bytes using xhtml2pdf.
    Returns bytes on success or None if generation fails.
    """
    try:
        from xhtml2pdf import pisa
    except Exception:
        return None

    html = get_template("certificates/certificate_pdf.html").render({"certificate": certificate})
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result, encoding="UTF-8")
    if pisa_status.err:
        return None
    return result.getvalue()


def verify(request):
    code = request.GET.get("code")
    cert = None
    if code:
        cert = Certificate.objects.filter(serial=code).select_related("user", "course").first()
    return render(request, "certificates/verify.html", {"certificate": cert, "code": code or ""})


def certificate_pdf(request, pk):
    """
    Stream a PDF for the given certificate.
    Access limited to the certificate owner, course instructor, or staff/admin.
    """
    certificate = get_object_or_404(
        Certificate.objects.select_related("user", "course", "course__instructor"),
        pk=pk,
    )

    user = request.user
    allowed = (
        user.is_authenticated
        and (
            user == certificate.user
            or user.is_staff
            or getattr(user, "role", "") == "admin"
            or certificate.course.instructor_id == user.id
        )
    )
    if not allowed:
        return HttpResponseForbidden("You do not have permission to view this certificate.")

    pdf_bytes = _render_pdf(certificate)
    if not pdf_bytes:
        # graceful fallback to HTML if PDF cannot be generated (e.g., missing xhtml2pdf)
        return render(request, "certificates/certificate_pdf.html", {"certificate": certificate})

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename=\"certificate-{certificate.serial}.pdf\"'
    return response

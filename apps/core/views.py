from django.shortcuts import render, redirect
from django.urls import reverse


def maintenance(request):
    return render(request, 'pages/maintenance.html')


def roleselection(request):
    """
    Role selection page for unauthenticated users; redirects to appropriate registration
    while preserving ?next= for post-login redirect.
    """
    next_url = request.GET.get("next") or request.POST.get("next")
    # When coming from an enroll flow, default to student registration directly
    if request.method == "GET" and next_url:
        target = f"{reverse('accounts:register_student')}?next={next_url}"
        return redirect(target)
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
                {"error": "Please select a role to continue.", "next": next_url or ""},
            )
        if next_url:
            target = f"{target}?next={next_url}"
        return redirect(target)
    return render(request, 'accounts/Role Selection for Registration.html', {"next": next_url or ""})

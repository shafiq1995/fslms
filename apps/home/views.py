from django.shortcuts import render
from django.apps import apps
from django.db.models import Count


def home(request):
    Course = apps.get_model('courses', 'Course')
    User = apps.get_model('accounts', 'User')
    Blog = None
    Blog = apps.get_model('blog', 'Post') if apps.is_installed('apps.blog') else None
    FAQ = apps.get_model('faq', 'FAQ') if apps.is_installed('apps.faq') else None

    # Popular courses: published/approved ordered by enrollments
    popular_courses = []
    if Course:
        try:
            popular_courses = (
                Course.objects.filter(status__in=["approved", "published", "Approved", "Published"])
                .annotate(enrolled_count=Count("enrollments"))
                .order_by("-enrolled_count", "-created_at")[:6]
            )
        except Exception:
            popular_courses = Course.objects.all().order_by("-created_at")[:6]

    instructors = (
        User.objects.filter(role='instructor', is_active=True)
        .order_by('-date_joined')[:4]
    )
    blogs = Blog.objects.order_by('-created_at')[:3] if Blog else []
    blogs_sample = []
    if (not Blog) or (not blogs):
        from types import SimpleNamespace
        blogs_sample = [
            SimpleNamespace(
                title="5 Tips to Ace Your Next Live Online Class",
                excerpt="Structure your prep, test your tech, and engage with your instructor to get the most out of every session.",
                published_at=None,
                comment_count=0,
                image=None,
                url="#",
            ),
            SimpleNamespace(
                title="Building Career-Ready Skills with FS LMS",
                excerpt="From project-based modules to instructor feedback, learn how to bridge the gap between theory and practice.",
                published_at=None,
                comment_count=0,
                image=None,
                url="#",
            ),
            SimpleNamespace(
                title="Why Manual Progress Tracking Matters for Live Classes",
                excerpt="Our non-streaming model empowers instructors to tailor pacing and recognize real completion milestones.",
                published_at=None,
                comment_count=0,
                image=None,
                url="#",
            ),
        ]
    # Show all active FAQs (ordered), no artificial slice so admins see every item they create
    faqs = FAQ.objects.filter(is_active=True).order_by('order', '-created_at') if FAQ else []
    faqs_sample = []
    if (not FAQ) or (not faqs):
        faqs_sample = [
            {"question": "How do live classes work?", "answer": "You’ll receive a join link with schedule details. Instructors mark completion manually after each session."},
            {"question": "When will I get access after payment?", "answer": "Once an admin approves your payment, your enrollment is activated and lessons unlock."},
            {"question": "Can I learn without videos?", "answer": "Yes. Courses focus on live/offline sessions and resources; instructors track progress per lesson."},
            {"question": "How do I become an instructor?", "answer": "Register as an instructor, complete your profile, and wait for admin approval before publishing courses."},
        ]

    # stats
    stats = {
        'students': User.objects.filter(role='student').count(),
        'courses': Course.objects.count() if Course else 0,
        'instructors': User.objects.filter(role='instructor').count(),
        'countries': 1,  # replace with real metric if available
    }

    course_categories = apps.get_model('courses', 'Category').objects.all()[:8] if apps.is_installed('apps.courses') else []

    context = {
        'courses': popular_courses,
        'instructors': instructors,
        'blogs': blogs,
        'blogs_sample': blogs_sample,
        'faqs': faqs,
        'faqs_sample': faqs_sample,
        'stats': stats,
        'course_categories': course_categories,
        'about_intro': "FS LMS is a premier online learning platform dedicated to providing high-quality education.",
    }
    return render(request, 'home.html', context)


def privacy(request):
    return render(request, "pages/privacy.html")


def terms(request):
    return render(request, "pages/terms.html")


def cookie_policy(request):
    return render(request, "pages/cookie_policy.html")

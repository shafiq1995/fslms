from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from .models import Post
from .forms import PostForm

def is_staff_or_admin(user):
    return user.is_authenticated and (user.is_staff or getattr(user, "role", "") == "admin")

def _paginate(request, qs, extra_context=None):
    paginator = Paginator(qs, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    recent = Post.objects.filter(published=True).order_by("-created_at")[:5]
    ctx = {"posts": page_obj, "page_obj": page_obj, "recent_posts": recent}
    if extra_context:
        ctx.update(extra_context)
    return ctx

def post_list(request):
    qs = Post.objects.filter(published=True).order_by("-created_at")
    q = request.GET.get("q", "").strip()
    tag = request.GET.get("tag", "").strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q) | Q(excerpt__icontains=q))
    if tag:
        qs = qs.filter(tags__icontains=tag)
    ctx = _paginate(request, qs, {"q": q, "tag": tag})
    return render(request, "blog/Blog List.html", ctx)


def post_archive(request, year, month):
    qs = Post.objects.filter(published=True, created_at__year=year, created_at__month=month).order_by("-created_at")
    ctx = _paginate(request, qs, {"archive_year": year, "archive_month": month})
    return render(request, "blog/Blog List.html", ctx)


def post_tag(request, tag):
    qs = Post.objects.filter(published=True, tags__icontains=tag).order_by("-created_at")
    ctx = _paginate(request, qs, {"tag": tag})
    return render(request, "blog/Blog List.html", ctx)


def post_detail(request, slug):
    if request.user.is_authenticated and request.user.is_staff:
        post = get_object_or_404(Post, slug=slug)
    else:
        post = get_object_or_404(Post, slug=slug, published=True)
    recent = Post.objects.filter(published=True).exclude(id=post.id).order_by("-created_at")[:5]
    return render(request, "blog/Blog Detail.html", {"post": post, "recent_posts": recent})


@login_required
@user_passes_test(is_staff_or_admin)
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            try:
                return redirect(reverse("admin_tools:blog_admin_list"))
            except Exception:
                return redirect(reverse("blog:list"))
    else:
        form = PostForm()
    return render(request, "blog/post_form.html", {"form": form, "is_edit": False})


@login_required
@user_passes_test(is_staff_or_admin)
def post_edit(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            try:
                return redirect(reverse("admin_tools:blog_admin_list"))
            except Exception:
                return redirect(reverse("blog:list"))
    else:
        form = PostForm(instance=post)
    return render(request, "blog/post_form.html", {"form": form, "is_edit": True, "post": post})

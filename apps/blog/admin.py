from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "published", "created_at", "is_featured")
    list_filter = ("published", "author", "is_featured", "category")
    search_fields = ("title", "content", "excerpt", "tags")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


# ========== User Admin ==========
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Roles and Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_approved', 'groups', 'user_permissions')
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2'),
        }),
    )

    list_display = ('username', 'email', 'role', 'is_approved', 'is_staff', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff', 'is_approved')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)


# ========== UserProfile Admin ==========
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_role', 'phone', 'country', 'is_verified', 'created_at')
    list_filter = ('user__role', 'is_verified', 'country')  # ✅ Use related field
    search_fields = ('user__username', 'user__email', 'phone', 'country')
    ordering = ('-created_at',)

    def get_role(self, obj):
        return obj.user.role
    get_role.short_description = 'Role'

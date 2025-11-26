from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    # path('', TemplateView.as_view(template_name='pages/home.html'), name='home'),
    path("accounts/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("courses/", include(("apps.courses.urls", "courses"), namespace="courses")),
    # path('enrollments/', include('apps.enrollments.urls', namespace='enrollments')),
    path('certificates/', include('apps.certificates.urls', namespace='certificates')),
    path('blog/', include('apps.blog.urls', namespace='blog')),
    path("admin-panel/", include(("apps.admin_tools.urls", "admin_tools"), namespace="admin_tools")),
    path("payments/", include(("apps.payments.urls", "payments"), namespace="payments")),
    path("roleselection/", include(("apps.core.urls", "roleselection"), namespace="roleselection")),
    # path('instructor/', include('apps.instructor_tool.urls', namespace='instructor_tool')),
    path("instructor/", include(("apps.instructor_tool.urls", "instructor_tool"), namespace="instructor_tool")),
    path('student/', include('apps.student_tool.urls', namespace='student_tool')),
    path('', include(('apps.home.urls','home'), namespace='home')),

]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

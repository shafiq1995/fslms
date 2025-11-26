from django.urls import path
from . import views
app_name='enrollments'
urlpatterns=[
    path('confirm/<slug:course_slug>/', views.enroll_confirm, name='confirm'),
    path('my/', views.my_enrollments, name='my_enrollments')
]

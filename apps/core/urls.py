from django.urls import path
from . import views
urlpatterns=[
    path('', views.roleselection, name='roleselection'),
    path('maintenance/', views.maintenance, name='maintenance'),

]

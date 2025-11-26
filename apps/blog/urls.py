from django.urls import path
from . import views
app_name='blog'
urlpatterns=[
    path("", views.post_list, name="list"),
    path("archive/<int:year>/<int:month>/", views.post_archive, name="archive"),
    path("tag/<slug:tag>/", views.post_tag, name="tag"),
    path("create/", views.post_create, name="create"),
    path("<slug:slug>/edit/", views.post_edit, name="edit"),
    path("<slug:slug>/", views.post_detail, name="detail"),
]

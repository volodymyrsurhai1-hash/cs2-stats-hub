from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('match/<str:match_id>/', views.match_room, name='match_room'),
]
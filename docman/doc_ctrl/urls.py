from django.urls import path

from . import views

app_name = 'doc_ctrl'

urlpatterns = [
    path('', views.doc_list, name='doc_list'),
    path('create/', views.doc_create, name='doc_create'),
    path('<int:pk>/detail/', views.doc_detail, name='doc_detail'),
    path('<int:pk>/edit/', views.doc_edit, name='doc_edit'),
    path('<int:pk>/delete/', views.doc_delete, name='doc_delete'),
]
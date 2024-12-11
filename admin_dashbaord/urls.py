from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='admin-dashboard'),
    path('get-users/', views.get_all_users, name='get-all-users'),
    path('add-document/', views.add_document, name='add-document'),
    path('see-document/', views.see_document, name='see-document'),
    path('delete-document/', views.delete_document, name='delete-document'),
    path('run-scrapper/', views.run_scrapper, name='run-scrapper'),
    path('get-scrapper-status/', views.get_scrapper_status, name='get-scrapper-status'),
]

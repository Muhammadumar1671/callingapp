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
    path('cancel-scrapper/', views.cancel_scrapper, name='cancel-scrapper'),
    path('get-scrapped-files/', views.get_all_scrapped_files, name='get-all-scrapped-files'),
    path('download-scrapped-file/<str:filename>/', views.download_scrapped_file, name='download-scrapped-file'),    
    path('get-scrapped-file/<str:filename>/', views.get_all_scrapped_files, name='get-scrapped-file'),

    path('split-csv/', views.split_csv, name='split-csv'),

]

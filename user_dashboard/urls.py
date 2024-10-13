from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_dashboard, name='user_dashboard'),
    path('api/get_csv_files/', views.get_csv_files, name='get_csv_files'),
    path('api/get_csv_data/<str:filename>/', views.get_csv_data, name='get_csv_data'),
    path('api/update_csv/', views.update_csv, name='update_csv'),
]

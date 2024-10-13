from django.urls import path
from . import views

app_name = "authorization"

urlpatterns = [
    path("", views.login_page, name="login_page"),
    path("signup/", views.signup_page, name="signup_page"),
    path('api/login/', views.login, name='login'),
    path('api/signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
]

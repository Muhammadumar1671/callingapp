from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from .serializer import CustomUserSerializer as UserSerializer
from .models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model, authenticate, logout
from django.middleware.csrf import get_token
from .tokens import account_activation_token
import logging
from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import redirect


User = get_user_model()
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    email = request.data.get('email')
    username = request.data.get('username')
    password = request.data.get('password')
    role = request.data.get('role')


    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists. Please use a different email.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({'message': 'User created successfully.'}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    
    password = request.data.get('password')
    username = User.objects.get(email=email).username
    print('email', email)
    print('password', password)
    user = authenticate(request, username=username, password=password)
    print('user', user)
    if user is not None:
        auth_login(request, user)
        csrf_token = get_token(request)  
        print('csrf_token', csrf_token)
        if user.role == 'admin':
         return Response({
            'message': 'Login successful',
                'csrf_token': csrf_token,
                'redirect_url': '/admin-dashboard/'  
            }, status=status.HTTP_200_OK)
        elif user.role == 'user':
            return Response({
                'message': 'Login successful',
                'csrf_token': csrf_token,
                'redirect_url': '/user-dashboard/'  
            }, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([AllowAny])
def login_page(request):
    return render(request, 'auth/login.html')

@api_view(['GET'])
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)
    return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

def signup_page(request):
    return render(request, 'auth/signup.html')


    

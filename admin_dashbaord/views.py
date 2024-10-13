from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import HttpResponseForbidden, HttpResponseServerError
from authorization.models import User
from authorization.serializer import CustomUserSerializer
from rest_framework.response import Response
from rest_framework import status
import os


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):    
    if request.user.role == 'admin':
        try:
            # Render the admin dashboard if the user is authenticated and an admin
            return render(request, 'admin/landingpage.html')
        except Exception as e:
            print(e)
            return HttpResponseServerError("An error occurred.")
    else:
        return HttpResponseForbidden("You don't have permission to access this page.")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    users = User.objects.filter(role='user')
    print(users)
    serializer = CustomUserSerializer(users, many=True)
    return Response({'users': serializer.data}, status=status.HTTP_200_OK)




import os
from django.conf import settings

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_document(request):
    document = request.FILES.get('document')
    username = request.POST.get('username')
    
    if not document or not username:
        return Response({'error': 'No document or username provided.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not document.name.endswith('.csv'):
        return Response({'error': 'Only CSV files are allowed.'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = get_object_or_404(User, username=username)
    
    # Define the base directory and user-specific directory
    user_directory = os.path.join(settings.MEDIA_ROOT, 'documents', str(user.username))
    
    # Create the directory if it doesn't exist
    os.makedirs(user_directory, exist_ok=True)
    
    # Save the document in the user's directory
    document_path = os.path.join(user_directory, document.name)
    
    try:
        with open(document_path, 'wb+') as destination:
            for chunk in document.chunks():
                destination.write(chunk)
    except Exception as e:
        return Response({'error': f'Failed to save document: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({'message': 'Document uploaded successfully'}, status=status.HTTP_201_CREATED)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def see_document(request):
    username = request.GET.get('username')
    print('username'   ,username)
    if not username:
        return Response({'error': 'No username provided.'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = get_object_or_404(User, username=username)
    
    # Construct the path to the user's documents folder
    user_documents_path = os.path.join(settings.MEDIA_ROOT, 'documents', user.username)

    # Check if the directory exists, if not return a 404
    if not os.path.exists(user_documents_path):
        return Response({'error': 'Documents not found.'}, status=status.HTTP_404_NOT_FOUND)

    # List the files in the user's document directory
    documents = os.listdir(user_documents_path)
    return Response({'documents': documents}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_document(request):
    document_name = request.data.get('document_name')
    username = request.data.get('username')
    
    if not document_name or not username:
        return Response({'error': 'Document name or username not provided.'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = get_object_or_404(User, username=username)
    
    # Construct the correct path to the user's document
    document_path = os.path.join(settings.MEDIA_ROOT, 'documents', str(user.username), document_name)
    
    if os.path.exists(document_path):
        try:
            os.remove(document_path)
            return Response({'message': 'Document deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Failed to delete document: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

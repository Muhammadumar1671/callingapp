from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import HttpResponseForbidden, HttpResponseServerError, FileResponse
from authorization.models import User
from authorization.serializer import CustomUserSerializer
from rest_framework.response import Response
from rest_framework import status
import os
from .models import ScrapperLoader
from .tasks import run_scrapper as run_scrapper_task
from celery.result import AsyncResult
from django.conf import settings
import pandas as pd
import zipfile
from datetime import datetime
import csv


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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_document(request):
    if 'document' not in request.FILES:
        return Response({'error': 'No document provided.'}, status=status.HTTP_400_BAD_REQUEST)
    
    document = request.FILES['document']
    username = request.POST.get('username')
    
    if not username:
        return Response({'error': 'No username provided.'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = get_object_or_404(User, username=username)
    
    # Create user's document directory if it doesn't exist
    user_documents_path = os.path.join(settings.MEDIA_ROOT, 'documents', str(user.username))
    os.makedirs(user_documents_path, exist_ok=True)
    
    try:
        # Read the content and process it line by line
        content = document.read().decode('utf-8').splitlines()
        processed_lines = []
        
        # Add headers if they don't exist
        headers = ['phone', 'name', 'address', 'website', 'services']
        if not content or not any(header in content[0].lower() for header in headers):
            processed_lines.append(','.join(headers))
        
        for line in content:
            parts = line.split(',', 4)  # Split into 5 parts
            
            # Clean up phone number format (first column)
            if parts[0]:
                # Remove brackets, quotes, and spaces, then extract just the numbers
                phone = ''.join(filter(str.isdigit, parts[0]))
                parts[0] = phone if phone else '123456'
            else:
                parts[0] = '123456'
            
            # Ensure all parts exist
            while len(parts) < 5:
                parts.append('')
            
            processed_lines.append(','.join(parts))
        
        # Save the processed content
        file_path = os.path.join(user_documents_path, document.name)
        with open(file_path, 'w', newline='') as f:
            f.write('\n'.join(processed_lines))
        
        return Response({'message': 'Document added successfully'}, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({'error': f'Error processing document: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

from redis import Redis
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_scrapper(request):
    states = request.data.get('states', [])
    categories = request.data.get('categories', [])
    print(states, categories)

    
    # Ensure states and categories are lists
    if not isinstance(states, list) or not isinstance(categories, list):
        return Response({'error': 'States and categories must be lists.'}, status=status.HTTP_400_BAD_REQUEST)
    
    run_scrapper_task.delay(states, categories)
    return Response({'message': 'Scrapper started'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_scrapper_status(request):
    scrapper = ScrapperLoader.objects.first()
    if scrapper:
        return Response({'message': scrapper.scrapper_status}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Scrapper not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_scrapper(request):
    try:
        # Get the running scrapper instance
        scrapper = ScrapperLoader.objects.first()
        if not scrapper:
            return Response({'message': 'No active scrapper found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Revoke the Celery task
        if scrapper.task_id:
            task = AsyncResult(scrapper.task_id)
            task.revoke(terminate=True)
            scrapper.scrapper_status = "Cancelled"
            scrapper.save()
            scrapper.delete()
            return Response({'message': 'Scrapper cancelled successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No task ID found'}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({'error': f'Failed to cancel scrapper: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_scrapped_files(request):
    files = os.listdir(os.path.join(settings.MEDIA_ROOT, 'scrappedfiles'))
    return Response({'files': files}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_scrapped_file(request, filename):
    try:
        file_path = os.path.join(settings.MEDIA_ROOT, 'scrappedfiles', filename)
        print(file_path)
        if os.path.exists(file_path):
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Delete the file after sending it
            os.remove(file_path)
            
            return response
        else:
            return Response(
                {'error': 'File not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {'error': f'Error downloading file: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def ensure_scrappedfiles_directory():
    scrapped_files_dir = os.path.join(settings.MEDIA_ROOT, 'scrappedfiles')
    os.makedirs(scrapped_files_dir, exist_ok=True)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def split_csv(request):
    if request.user.role != 'admin':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        csv_file = request.FILES.get('csv_file')
        row_distribution = request.POST.get('row_distribution', '')
        
        if not csv_file:
            return Response({'error': 'No CSV file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not csv_file.name.endswith('.csv'):
            return Response({'error': 'File must be a CSV'}, status=status.HTTP_400_BAD_REQUEST)

        # Parse row distribution
        try:
            rows_per_file = [int(x) for x in row_distribution.split(',') if x.strip()]
        except ValueError:
            return Response({'error': 'Invalid row distribution format'}, status=status.HTTP_400_BAD_REQUEST)

        # Read the CSV file using csv module instead of pandas
        csv_content = csv_file.read().decode('utf-8').splitlines()
        header = csv_content[0]  # Get the header row
        data_rows = csv_content[1:]  # Get all data rows
        total_rows = len(data_rows)
        
        # Validate if we have enough rows
        if sum(rows_per_file) > total_rows:
            return Response({
                'error': f'Not enough rows in CSV. File has {total_rows} rows, but distribution requires {sum(rows_per_file)} rows'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create user-specific directory for split files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        user_dir = os.path.join(settings.MEDIA_ROOT, 'documents', str(request.user.username), 'split_files', timestamp)
        os.makedirs(user_dir, exist_ok=True)
        
        # Split the data according to the distribution
        split_files = []
        current_row = 0
        
        for i, num_rows in enumerate(rows_per_file):
            # Create split CSV file
            split_filename = f'split_{i + 1}.csv'
            split_path = os.path.join(user_dir, split_filename)
            
            # Get the rows for this split
            split_rows = data_rows[current_row:current_row + num_rows]
            current_row += num_rows
            
            # Write the split file with header and data
            with open(split_path, 'w', newline='') as f:
                f.write(header + '\n')  # Write header
                f.write('\n'.join(split_rows))  # Write data rows
            
            split_files.append(split_path)
        
        # Create ZIP file
        zip_filename = f'split_files_{timestamp}.zip'
        zip_path = os.path.join(user_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in split_files:
                zipf.write(file, os.path.basename(file))
        
        # Clean up individual split files
        for file in split_files:
            os.remove(file)
        
        # Return the ZIP file
        response = FileResponse(open(zip_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
        
        # Clean up zip file after sending
        os.remove(zip_path)
        os.rmdir(user_dir)
        
        return response
        
    except Exception as e:
        return Response({'error': f'Error splitting CSV: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
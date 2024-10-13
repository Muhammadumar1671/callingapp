from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import csv
import os

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    return render(request, 'user/userpage.html')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_csv_files(request):
    username = request.user.username
    csv_dir = f'documents/{username}'
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    return JsonResponse({'csv_files': csv_files})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_csv_data(request, filename):
    username = request.user.username  # Use the authenticated user's username
    csv_path = f'documents/{username}/{filename}'
    data = []
    try:
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            if 'called' not in fieldnames:
                fieldnames.append('called')
            if 'notes' not in fieldnames:
                fieldnames.append('notes')

            for row in reader:
                if 'called' not in row:
                    row['called'] = 'No'
                if 'notes' not in row:
                    row['notes'] = ''
                data.append(row)
    except FileNotFoundError:
        return JsonResponse({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    return JsonResponse({'data': data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_csv(request):
    username = request.user.username
    data = request.data  # Use request.data instead of json.loads(request.body)
    filename = data['filename']
    phone = data['phone']
    notes = data['notes']
    csv_path = f'documents/{username}/{filename}'
    
    # Read existing data and check for 'called' and 'notes' fields
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        if 'called' not in fieldnames:
            fieldnames.append('called')
        if 'notes' not in fieldnames:
            fieldnames.append('notes')
        
        updated_rows = []
        for row in reader:
            if row['phone'] == phone:
                row['called'] = 'Yes'
                row['notes'] = notes
            elif 'called' not in row:
                row['called'] = 'No'
            if 'notes' not in row:
                row['notes'] = ''
            updated_rows.append(row)
    
    # Write updated data back to CSV
    with open(csv_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)
    
    return JsonResponse({'status': 'success'})

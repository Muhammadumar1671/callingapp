from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import csv
import os
from .models import Leads
from django.utils.dateparse import parse_datetime

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
    try:
        data = request.data
        required_fields = ['phone', 'name', 'address', 'services', 'notes']
        
        # Validate required fields
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }, status=400)

        phone = data['phone']
        notes = data['notes']
        
        # Extract status and follow-up date from notes
        status = 'Not Called'
        follow_up_date = None
        
        if 'Lead Successfully Converted!' in notes:
            status = 'Converted'
        elif 'Interested' in notes:
            status = 'Interested'
            if '(Follow-up scheduled for:' in notes:
                date_str = notes.split('(Follow-up scheduled for:')[1].split(')')[0].strip()
                follow_up_date = parse_datetime(date_str)
        elif 'Not Interested' in notes:
            status = 'Not Interested'
        elif 'Call Back Later' in notes:
            status = 'Call Back'

        # Try to get existing lead or create new one
        lead, created = Leads.objects.get_or_create(
            business_phone=phone,
            user=request.user,
            defaults={
                'business_name': data['name'],
                'business_address': data['address'],
                'business_services': data['services'],
                'notes': notes,
                'status': status,
                'called': True,
                'follow_up_date': follow_up_date
            }
        )
        
        if not created:
            # Update existing lead with all fields
            lead.business_name = data['name']
            lead.business_address = data['address']
            lead.business_services = data['services']
            lead.notes = notes
            lead.status = status
            lead.called = True
            lead.follow_up_date = follow_up_date
            lead.save()

        # Update CSV file
        csv_update_response = update_csv_file(
            request.user.username,
            data['filename'],
            phone,
            notes
        )
        
        return JsonResponse({
            'status': 'success',
            'lead_id': lead.id,
            'csv_update': csv_update_response
        })

    except Exception as e:
        print(f"Error in update_csv: {str(e)}")  # Add logging for debugging
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def update_csv_file(username, filename, phone, notes):
    # Original CSV update logic
    csv_path = f'documents/{username}/{filename}'
    
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
    
    with open(csv_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)
    
    return 'success'


import os
from groq import Groq
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_script(request):
    try:
        data = request.data
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Format business info for the prompt
        business_info = f"""
            Business Name: {data.get('name', 'Not provided')}
            Address: {data.get('address', 'Not provided')}
            Services: {data.get('services', 'Not provided')}
            Previous Notes: {data.get('notes', 'No previous notes')}
            """

        prompt = f"""
            You are a professional sales representative working for a digital software marketing company. Your task is to draft a natural and engaging cold-call script for the following business:

            {business_info}

            Here are the requirements for the script:
            1. Start with a professional and friendly introduction, mentioning your name and company. The caller's name is {request.data.get('username')}.
            2. Clearly state the purpose of your call, focusing on how your company helps businesses improve through digital software solutions.
            3. Politely inquire about the business's current software solutions and challenges.
            4. Guide the conversation toward understanding their specific needs or pain points.
            5. Use a conversational and concise tone to keep the business owner engaged.
            6. Include adaptable follow-up questions based on possible responses.
            7. Conclude with a clear call-to-action (e.g., scheduling a follow-up meeting, providing more information, etc.).

            The script should be divided into the following sections:
            - **Introduction:** How the conversation begins.
            - **Key Questions:** Core inquiries to understand the business's needs.
            - **Possible Responses:** Anticipated answers and how to handle them.
            - **Next Steps:** How to close the conversation with actionable items.

            Ensure the tone is approachable yet professional to foster a positive impression.
            """

        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an experienced sales script writer specializing in B2B software sales."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=1024,
        )
        
        script = chat_completion.choices[0].message.content
        
        return JsonResponse({
            'status': 'success',
            'script': script
        })
    except Exception as e:
        print(f"Error generating script: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def script_page(request):
    return render(request, 'user/script_page.html')




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_reminder_email(request):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from django.conf import settings
    
    try:
        data = request.data
        recipient_email = data.get('email')
        follow_up_date = data.get('follow_up_date')
        business_name = data.get('business_name')
        
        if not all([recipient_email, follow_up_date, business_name]):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields'
            }, status=400)

        # Email setup
        sender_email = os.environ.get('email_user')
        password = os.environ.get('password')

        # Create message
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = f'Follow-up Reminder: {business_name}'

        # Email body
        body = f"""
        Hello,

        This is a reminder about your scheduled follow-up with {business_name} on {follow_up_date}.

        Best regards,
        Digital Software Marketing Team
        """
        
        message.attach(MIMEText(body, 'plain'))

        # Create SMTP session
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            text = message.as_string()
            server.sendmail(sender_email, recipient_email, text)

        return JsonResponse({
            'status': 'success',
            'message': 'Reminder email sent successfully'
        })

    except Exception as e:
        print(f"Error sending reminder email: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)




    
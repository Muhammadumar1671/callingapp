From python:3.11-slim

#set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#SET WORKING DIRECTORY
WORKDIR /app

#copy requirements.txt
COPY requirements.txt .

#install dependencies
RUN pip install -r requirements.txt

#copy project
COPY . /app/

#collect static files
RUN python3.11 manage.py collectstatic --noinput

#Expose port 8000 to the outside world
EXPOSE 8000

#Run the application
CMD ["sh", "-c", "python3.11 manage.py runserver 0.0.0.0:8000"]





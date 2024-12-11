from django.db import connections
from celery.signals import worker_process_init

@worker_process_init.connect
def close_db_connections(**kwargs):
    for conn in connections.all():
        conn.close()

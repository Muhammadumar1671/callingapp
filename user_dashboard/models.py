from django.db import models
from authorization.models import User

class Leads(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=255)
    business_address = models.TextField()
    business_services = models.TextField()
    business_phone = models.CharField(max_length=50, unique=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=50, default='Not Called')
    called = models.BooleanField(default=False)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Leads"
        indexes = [
            models.Index(fields=['business_phone']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.business_name} - {self.business_phone}"


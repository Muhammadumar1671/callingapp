from django.db import models

class ScrapperLoader(models.Model):
    scrapper_status = models.CharField(max_length=255, default='idle')
    scrapper_status_message = models.TextField(default='')
    
    @classmethod
    def create_scrapper_loader(self):
        loader = ScrapperLoader.objects.create(scrapper_status='running')
        loader.save()
        return loader

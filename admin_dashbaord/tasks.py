# run the scrapper
from admin_dashbaord.models import ScrapperLoader
from CallingApp.scrappingscript import BusinessScraper
from celery import shared_task
import multiprocessing

#multiprocssing
multiprocessing.set_start_method('spawn', force=True)




@shared_task
def run_scrapper(states, categories):
    print('starteddd')
    scrapper = ScrapperLoader.create_scrapper_loader()
    # Store the task ID
    scrapper.task_id = run_scrapper.request.id
    scrapper.save()
    scraper = BusinessScraper()
    scraper.scrape_businesses(categories, states)
    scrapper.delete()

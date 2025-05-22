from celery import shared_task

@shared_task
def send_license_report():
    print("Generating license report...")
    return True

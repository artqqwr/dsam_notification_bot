from datetime import datetime
from telegram.ext import CallbackContext

from handlers import services
import models

async def delete_expired_keys(context: CallbackContext) -> None:
    for key in list(models.Key):
        models.Key.delete_by_id(key.uuid)

async def add_notifications_to_job_queue(context: CallbackContext) -> None:
    for notification in list(models.Notification):
        async def job(callback):
            await services.send_event_for_all(context.bot, notification.event, context)
            n = models.Notification.get_or_none(notification.id)
            if n:
                n.delete_instance()
        job_name = str(notification.id) + str(notification.event.id)
        context.job_queue.run_once(job, notification.date, name=job_name)

async def delete_lost_notifications(context: CallbackContext) -> None:
    lost_notifications: list[models.Notification] = models.Notification.select().where(
        models.Notification.date < datetime.today().replace(day=datetime.today().day+1)).get_or_none()
    
    if not lost_notifications:
        return
    
    for notification in lost_notifications:
        notification.delete_instance()
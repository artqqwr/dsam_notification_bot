
from os import path
import shutil
from telegram import Bot, InputMediaDocument, InputMediaPhoto, InputMediaVideo, error
from telegram.ext import CallbackContext

import config
import models
import template


EVENT_EXAMPLE = {
    'name': 'Эко-акция в Несветает',
    'date': '22.09.2024 09:00',
    'text': '22 сентября в селе Несветай пройдёт традиционная для ДСАМ эко-акция на территории церкви Сурб Карапет.'
}


def delete_event(event_id: int, context):
    event: models.Event = models.Event.get_by_id(event_id)
    for notification in list(event.notifications):
        job_name = str(notification.id) + str(event.id)
        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
        notification.delete_instance()
    
    for file in list(event.files):
        file.delete_instance()

    for type in ['photo', 'document', 'video']:
        try:
            shutil.rmtree(path.join(config.UPLOADS_PATH,
                            type, f'{event.id}'))
        except FileNotFoundError:
            continue

    event.delete_instance()

async def send_event_for_all(bot: Bot, event: models.Event, context: CallbackContext) -> None:
    users = list(models.User)

    types = {
        'photo': InputMediaPhoto,
        'document': InputMediaDocument,
        'video': InputMediaVideo,
    }

    sended = {}

    event.date = event.date.strftime(config.DATE_FORMAT)

    for user in users:
        text = template.render('event', event=event)
        media_group = []
        for file in event.files:
            media_group.append(
                types[file.type](open(file.src, 'rb'))
            )

        message = None
        try:
            if media_group:
                message = await bot.send_media_group(chat_id=user.id, media=media_group, caption=text)
                message = message[0]
            else:
                message = await bot.send_message(chat_id=user.id, text=text)

            sended[user.id] = message.id

        except error.BadRequest:
            models.User.delete_by_id(user.id)

    context.user_data['sended'] = sended



def set_last_message(context: CallbackContext, message):
    if not 'last_message' in context.user_data.keys():
        context.user_data['last_message'] = [message]

    context.user_data['last_message'].append(message)
    if len(context.user_data['last_message']) == 3:
        context.user_data['last_message'] = context.user_data['last_message'][1:]


# def set_last_message(context: CallbackContext, message, kb):
#     if not 'last_message' in context.user_data.keys():
#         context.user_data['last_message'] = [message]

#     context.user_data['last_message'].append(message)
#     if len(context.user_data['last_message']) == 3:
#         context.user_data['last_message'] = context.user_data['last_message'][1:]

#     if not 'last_menu' in context.user_data.keys():
#         context.user_data['last_menu'] = [kb]

#     context.user_data['last_menu'].append(kb)
#     if len(context.user_data['last_menu']) == 3:
#         context.user_data['last_menu'] = context.user_data['last_menu'][1:]
from datetime import datetime
from typing import Dict, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update, error
from telegram.ext import CallbackContext

import config
from handlers import services
from handlers.services import delete_event, send_event_for_all
from handlers.states_processing import ProcessingStates
import models
from template import render
from ui import buttons, keyboards


async def handle_inline(update: Update, context: CallbackContext):
    query = update.callback_query
    callbacks: Dict[str | function] = {
        'add_event_files': _add_files_event,
        'delete_event': _delete_event,
        'get_event_notifications_menu': _get_event_notifications_menu,
        'add_event_notifications': _add_event_notifications,
        'delete_last_event_notification': _delete_last_event_notification,
        'back': _back,
        'delete_message_from_user': _delete_message_from_user,
    }

    if '#' in query.data:
        callback_name = query.data.split('#')[0]
        data = query.data.split('#')[1]
        data = data.split('&') 

        return await callbacks[callback_name](update, context, data)
    await callbacks[query.data](update, context)


async def _delete_message_from_user(update: Update, context: CallbackContext):
    await update.callback_query.delete_message()
    
    sended = context.user_data.get('sended')
    if sended:
        for user_id, message_id in sended.items():
            try:
                await update.get_bot().delete_message(user_id, message_id)
            except error.BadRequest:
                continue

    await update.callback_query.answer('Удалено')

async def _back(update: Update, context: CallbackContext):
    if not context.user_data.get('last_message'):
        return await update.callback_query.delete_message()

    message = context.user_data['last_message'][0]
    if message:
        await update.callback_query.edit_message_text(message.text, reply_markup=message.reply_markup)
        services.set_last_message(context, message)

# async def _back(update: Update, context: CallbackContext):
#     if not any([i in context.user_data.keys() for i in ['last_menu', 'last_message']]):
#         return await update.callback_query.delete_message()

#     menu = context.user_data['last_menu'][0]
#     message = context.user_data['last_message'][0]
#     if menu and message:
#         await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(menu))
#         services.set_last_message(context, message, menu)


async def _delete_last_event_notification(update: Update, context: CallbackContext, data: str):
    query = update.callback_query

    event_id = int(data[0])
    event = models.Event.get_or_none(event_id)
    if not event:
        await update.callback_query.delete_message()
        return await query.answer('Мероприятие не найдено')

    kb = keyboards.inline_notifications_type_menu(event_id)

    text = '\n'.join(query.message.text.split('\n')[:-1])
    notification: models.Notification = models.Notification.select().where(models.Notification.event ==
                                                                           event).order_by(models.Notification.id.desc()).get_or_none()

    if not notification or len(event.notifications) == 1 or notification.delete_instance() == 0:
        await query.answer('Больше нет уведомлений')
        text = text[:-1] + 'список пуст'
        kb = kb[1:]

    if notification:
        job_name = str(notification.id) + str(event.id)
        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()

        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(kb)
        )


async def _add_event_notifications(update: Update, context: CallbackContext, data: str):
    event_id = int(data[0])
    notification_type = int(data[1])
    event: models.Event = models.Event.get_or_none(id=event_id)
    if not event:
        await update.callback_query.delete_message()
        return await update.callback_query.answer('Такого мероприятия не существет')

    if notification_type == models.NotificationTypes.NOW:
        message: Message = await context.bot.send_message(update.effective_user.id, 'Отправляется...')
        await send_event_for_all(context.bot, event, context)
        return await message.edit_text(f'Мероприятие "{event.name}" отправлено', reply_markup=InlineKeyboardMarkup.from_button(
            buttons.INLINE_DELETE_MESSAGE_FROM_USER
        ))

    context.user_data['notification'] = models.Notification(
        type=notification_type, event=event)
    context.user_data['state'] = ProcessingStates.SET_NOTIFICATIONS_DATETIME

    format = 'HH:MM'
    if notification_type == models.NotificationTypes.CUSTOM:
        format = 'DD.MM.YYYY ' + format
    else:
        if notification_type == models.NotificationTypes.DAY_BEFORE:
            context.user_data['notification'].date = datetime(
                year=event.date.year, month=event.date.month, day=event.date.day-1, hour=9, minute=0)
        if notification_type == models.NotificationTypes.ON_DAY:
            context.user_data['notification'].date = datetime(
                year=event.date.year, month=event.date.month, day=event.date.day, hour=9, minute=0)
    await update.get_bot().send_message(update.callback_query.from_user.id, f'Напиши время уведомления в формате "{format}"')


async def _get_event_notifications_menu(update: Update, context: CallbackContext, data: str):
    query = update.callback_query
    event_id = int(data[0])
    event = models.Event.get_or_none(event_id)
    if not event:
        await update.callback_query.delete_message()
        return await query.answer('Мероприятие не найдено')

    kb = keyboards.inline_notifications_type_menu(event_id)

    text = '\n'.join(query.message.text.split('\n')[:2])+'\n\n'
    text += '<b>Уведомления: </b>'

    for notification in event.notifications:
        text += f'\n\n<b>- {models.NotificationTypes.get(notification.type)}</b> | <i>{notification.date.strftime(config.DATE_FORMAT)}</i>'
    if not event.notifications:
        text += 'cписок пуст'
        kb = kb[1:]


    message = await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb)
    )

    services.set_last_message(context, message)


async def _delete_event(update: Update, context: CallbackContext, data: str):
    event_id = int(data[0])
    query = update.callback_query

    try:
        event: models.Event = models.Event.get_by_id(event_id)
        delete_event(event_id, context)
        await query.answer(f'Мероприятие "{event.name}" удалено')
    except models.Event.DoesNotExist:
        await query.answer('Такого мероприятия не существет')

    await query.delete_message()


async def _add_files_event(update: Update, context: CallbackContext, data: str):
    event_id = int(data[0])
    await update.callback_query.answer(f'📁 Отправь файлы.')

    context.user_data['current_event'] = event_id
    context.user_data['state'] = ProcessingStates.ADD_FILES


async def hanlde_reply(update: Update, context: CallbackContext):
    text = update.message.text

    if text == keyboards.ADMIN_MENU[0][0].text:
        access_key = models.Key.create()
        url = f'https://t.me/share/url?url=https%3A%2F%2Ft.me%2F{config.BOT_NAME}%3Ftext%3D%2Fadmin%2520{access_key.uuid}'
        share_button = InlineKeyboardButton(
            text="Поделиться",
            url=url,
        )
        await update.message.reply_text(f'<b>Ключ:</b> <i>{access_key.uuid}</i>', reply_markup=InlineKeyboardMarkup.from_button(share_button))

    if text == keyboards.ADMIN_MENU[1][0].text:
        await update.message.reply_text(f'Напиши о мероприятии в таком форматие:\n\n{render("event_template")}')
        context.user_data['state'] = ProcessingStates.ADD_EVENT

    if text == keyboards.ADMIN_MENU[2][0].text:
        events: List[models.Event] = list(models.Event)
        await update.message.reply_text(
            render('events_list', {
                'events': events,
                'date_to_str': lambda date: date.strftime(config.DATE_FORMAT),
                'zip': zip
            })
        )

        context.user_data['state'] = ProcessingStates.SELECT_EVENT if events else None

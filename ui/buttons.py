from telegram import InlineKeyboardButton

from models import NotificationTypes


def inline_add_event_files(event_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton('Добавить файлы', callback_data=f'add_event_files#{event_id}')


def inline_send_event_now(event_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton('Отправить сейчас', callback_data=f'send_event_now#{event_id}')


def inline_delete_event(event_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton('Удалить', callback_data=f'delete_event#{event_id}')


def inline_get_event_notifications_menu(event_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton('Добавить уведомления', callback_data=f'get_event_notifications_menu#{event_id}')


def inline_add_event_notifications(notification_type: NotificationTypes, event_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(NotificationTypes.get(notification_type), callback_data=f'add_event_notifications#{event_id}&{notification_type}')


def inline_delete_last_event_notification(event_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton('Удалить последнее', callback_data=f'delete_last_event_notification#{event_id}')

INLINE_DELETE_MESSAGE_FROM_USER = InlineKeyboardButton('Удалить отправленное уведомление', callback_data='delete_message_from_user')
INLINE_BACK = InlineKeyboardButton('Назад', callback_data='back')

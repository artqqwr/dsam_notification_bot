from telegram import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from models import NotificationTypes
from ui import buttons


ADMIN_MENU = [
    [KeyboardButton('Сгенерировать ключ')],
    [KeyboardButton('Создать мероприятие')],
    [KeyboardButton('Список мероприятий')],
]


def inline_notifications_type_menu(event_id: int):
    return [
        [buttons.inline_delete_last_event_notification(event_id)],
        [buttons.inline_add_event_notifications(
            NotificationTypes.DAY_BEFORE, event_id)],
        [buttons.inline_add_event_notifications(
            NotificationTypes.ON_DAY, event_id)],
        [buttons.inline_add_event_notifications(
            NotificationTypes.NOW, event_id)],
        [buttons.inline_add_event_notifications(
            NotificationTypes.CUSTOM, event_id)],
        [buttons.INLINE_BACK],
    ]

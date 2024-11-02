from datetime import datetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackContext


from config import IS_DEBUG
from handlers import services
from models import Event, Key, User
from template import render
from ui import keyboards


async def stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user: User = User.get_or_none(id=update.effective_user.id)
    if user and user.is_admin:
        await update.message.reply_text(render('statistic', events_count=Event.select().where(Event.date > datetime.now()).count(),
                                               admins_count=User.select().where(User.is_admin == True).count(),
                                               users_count=User.select().count()))


async def cancel(update: Update, context: CallbackContext):
    context.user_data['state'] = None


async def event_example(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        render('event', event=services.EVENT_EXAMPLE)
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    User.get_or_create(id=update.effective_user.id)

    await update.message.reply_text(
        render('start')
    )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user: User = User.get_or_none(id=update.effective_user.id)

    await update.message.reply_text(
        render('help',
               is_admin=user.is_admin,
               is_debug=IS_DEBUG,
               )
    )


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    access_key = ''
    if context.args:
        access_key = context.args[0]

    await _admin(update, access_key)


async def _admin(update: Update, access_key: str):
    id = update.effective_user.id
    try:
        user: User = User.get_by_id(id)
        if not user.is_admin and Key.select().where(Key.uuid == access_key):
            user.is_admin = True
            user.save()

            await update.message.reply_text('✅ <b>Ты теперь администратор!</b>')
        if user.is_admin:
            await update.message.reply_text(render('admin'), reply_markup=ReplyKeyboardMarkup(keyboards.ADMIN_MENU, resize_keyboard=True))
        else:
            await update.message.reply_text(f'🚫 У тебя нет прав администратора.')
    except User.DoesNotExist:
        User.create(id=id)
        await _admin(update, access_key)

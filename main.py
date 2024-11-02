import logging
from pytz import timezone
from telegram.ext import ApplicationBuilder, Application, Defaults
from telegram.constants import ParseMode

import config
import database
import handlers

if config.IS_DEBUG:
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )


def main():
    database.connect()

    app: Application = ApplicationBuilder().token(config.TOKEN).defaults(
        Defaults(parse_mode=ParseMode.HTML, tzinfo=timezone('Europe/Moscow'))
    ).build()
    handlers.register(app)

    app.run_polling()

if __name__ == '__main__':
    main()

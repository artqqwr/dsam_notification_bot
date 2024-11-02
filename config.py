from os import getenv
from dotenv import load_dotenv 
load_dotenv()

TOKEN = getenv('TOKEN')

DATABASE_DSN = './database.db'
ROOT_USERS_ID = getenv('ROOT_USERS_ID').split(',')

IS_DEBUG = True
DATE_FORMAT = '%d.%m.%Y %H:%M'

TEMPLATES_PATH = './templates'
UPLOADS_PATH = './uploads'
EVENT_EXAMPLE_FILE_PATH = f'{UPLOADS_PATH}/photo/event_example.jpg'
DELETE_LOST_NOTIFICATIONS_TIME = '23:00'
DELETE_EXPIRED_KEYS_TIME = '23:00'
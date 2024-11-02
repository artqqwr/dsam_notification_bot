from peewee import *

import config
from models import MODELS, User

conn = SqliteDatabase(config.DATABASE_DSN)

def connect():
    for model in MODELS:
        model._meta.database = conn

    conn.connect()
    conn.create_tables(MODELS)

    for id in config.ROOT_USERS_ID:
        User.get_or_create(id=id, is_admin=True)

def close():
    conn.close()
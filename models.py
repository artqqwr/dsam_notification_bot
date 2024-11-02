import uuid

from peewee import *


class BaseModel(Model):
    class Meta:
        database = None


class Key(BaseModel):
    uuid = UUIDField(primary_key=True, default=uuid.uuid4)


class Event(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    text = TextField()
    date = DateTimeField()


class NotificationTypes:
    DAY_BEFORE = 1
    ON_DAY = 2
    NOW = 3
    CUSTOM = 4

    def get(id: int) -> str:
        match id:
            case 1:
                return 'За день до'
            case 2:
                return 'В день мероприятия'
            case 3:
                return 'Сейчас'
            case 4:
                return 'Другую дату'


class Notification(BaseModel):
    id = IntegerField(primary_key=True)
    type = IntegerField()
    date = DateTimeField()
    event = ForeignKeyField(
        Event, backref='notifications')

    class Meta:
        indexes = (
            (('type', 'date', 'event'), True),
        )


class File(BaseModel):
    id = IntegerField(primary_key=True)
    src = CharField()
    type = CharField()
    event = ForeignKeyField(Event, backref='files')


class User(BaseModel):
    id = IntegerField(primary_key=True)
    is_admin = BooleanField(default=False)


MODELS = [
    Event,
    File,
    Notification,
    User,
    Key,
]

from functools import wraps
from sqlalchemy import create_engine
from contextlib import contextmanager
from urllib.parse import quote

from sqlalchemy.orm import sessionmaker

from Config import configs

from DB.enums import DbName


def makeEngine(db_name: DbName):
    pw = quote(configs.get('postgres').get('password'))
    usr = configs.get('postgres').get('username')
    host = configs.get('postgres').get('host')
    port = configs.get('postgres').get('port')
    hostname = f'{host}:{port}' if port else host
    engineString = f'postgresql://{usr}:{pw}@{hostname}/{db_name.value}'
    engine = create_engine(engineString)
    return engine


def makeSession(db_name: DbName):
    return sessionmaker(bind=makeEngine(db_name))()


@contextmanager
def Session(db_name: DbName):
    ses = makeSession(db_name)
    try:
        yield ses
    finally:
        ses.close()


def withSession(db_name: DbName):
    def withSessionDecorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            SQLSession = makeSession(db_name)
            try:
                res = func(SQLSession, *args, **kwargs)
            finally:
                SQLSession.close()
            return res
        return wrapper
    return withSessionDecorator

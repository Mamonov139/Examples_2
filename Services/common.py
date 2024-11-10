from functools import reduce
from uuid import uuid4, UUID
from enum import Enum
from datetime import datetime, timedelta, timezone
from abc import ABC, abstractmethod

from sqlalchemy import func, and_
from sqlalchemy.orm import aliased
from sqlalchemy.sql.functions import coalesce, concat

from DB.models import Franchise, Clients, Object_x_Client, Transactions, EstimateObjects

TD3 = timedelta(hours=3)
MOSCOW = timezone(TD3)


def get_tochka_dt(dt_string):
    dt = datetime.strptime(dt_string, f"%Y-%m-%dT%H:%M:%S{'.%f' if '.' in dt_string else ''}%z")
    dt = dt.replace(tzinfo=MOSCOW) - timedelta(seconds=dt.utcoffset().seconds) + TD3
    return dt


def uuid():
    return str(uuid4())


def getItemByKeyChain(chain, dictionary, separator: str = '.'):
    """
    Проход словаря по цепочке ключей. Цепочка ключей строчка, разделённая указанным сепаратором

    Positional arguments:
    chain -- str, цепочка ключений, например ключ1.ключ2.ключ3
    dictionary -- dict, словарь в котором надо найти знаяение

    Keyword arguments:
    separator -- str, разделитель в строке separator (default: '.')

    Возвращает значение из словаря (тип соотвествует типу элемента в словаре)
    """
    keyList = chain.split(separator)
    try:
        val = reduce(lambda d, k: [d_[k] for d_ in d] if isinstance(d, list) else d[k], keyList, dictionary)
    except (KeyError, IndexError):
        return None
    return val


class ReqType(Enum):
    GET = 'get'
    POST = 'post'


class BeneficiaryType(Enum):
    UL = ("name", "kpp")
    IP = ("first_name", "middle_name", "last_name")
    FL = ("first_name", "middle_name", "last_name",
          "birth_date", "birth_place", "passport_series",
          "passport_number", "passport_date", "registration_address")

    @classmethod
    def find_beneficiary(cls, legal_status):
        return next(filter(lambda x: x.name == legal_status, cls), None)


class CityCode(Enum):
    SPB = 'spb'
    MSC = 'msc'


class ContentType(Enum):
    PDF = 'application/pdf'
    GIT = 'image/gif'
    JPEG = 'image/jpeg'
    PJPEG = 'image/pjpeg'
    PNG = 'image/png'
    TIFF = 'image/tiff'
    XTIFF = 'image/x-tiff'
    BMP = 'image/bmp'
    XWBPM = 'image/x-windows-bmp'
    XMBMP = 'image/x-ms-bmp'
    MBMP = 'image/ms-bmp'
    XBMP = 'image/x-bmp'

class ReportGroup(Enum):
    YOOKASSA = 'yookassa'


class MerchantGroup(Enum):
    REGULAR = 'regular'
    CREDIT = 'credit'


class ServiceError(Exception):
    default_detail = 'Internal service error'
    detail = ''

    def __init__(self, detail=None, status_code=None):
        if detail is None:
            detail = self.default_detail

        self.detail = detail
        self.status_code = status_code

    def __str__(self):
        return str(self.detail)


class ExpiredToken(ServiceError):
    default_detail = 'Истёк срок действия ключа'

class StatusPay(Enum):
    PAID = 'PAID'
    CANCELED = 'CANCELED'


class LifePayOperationType(Enum):
    SELL = 'payment'  # чек «Приход»
    SELL_REF = 'refund'  # чек «Возврат прихода»


class ServiceFactory(ABC):
    @classmethod
    @abstractmethod
    def create_from_user_id(cls, user_id, *args, **kwargs):
        """
        Создание службы через user_id

        :param user_id: идентификатор пользователя

        :return: объект службы
        """
        pass

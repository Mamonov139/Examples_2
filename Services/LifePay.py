import json
from abc import ABC, abstractmethod
from logging import Logger
from typing import Optional, TypeVar
from Logger import get_logger
from requests import session

from Config import configs
from DB import Session, DbName, rawRequest
from DB.models import Transactions, Report, AmoObjects, EstimateObjects
from Services.common import PaymentTypes
from .common import ServiceError, ServicesType, Merchant, PaymentMethod, PaymentObject, \
    ServiceFactory, LifePayOperationType, get_manual_prepayment, is_nominal_object
from AuthManager import RoleEnum

Logger_lifePay = get_logger('lifePay_payload', 'lifePay_payload')
SelfService = TypeVar('SelfService', bound='Service')


class Service(ServiceFactory):
    __API_URLS = configs.get('life_pay_urls')
    __MERCHANTS = configs.get('life_pay_mto')

    def __init__(self, merchant: Merchant = Merchant.DOMEO_MART, with_agent=True):
        self.__session = session()
        self.__session.headers.update({
            'Content-Type': 'application/json',
            'charset': 'utf-8',
        })
        self.scheme = None
        self.merchant = merchant
        self.with_agent = with_agent

    @classmethod
    def create_from_user_id(cls, user_id: int, *args, **kwargs) -> Optional[SelfService]:
        """
        :param user_id: идентификатор пользователя

        :return: объект службы LifePay
        """
        with_agent = kwargs.get('with_agent', True)

        if kwargs.get('merchant_id'):
            merchant = Merchant.find_merchant_by_id(kwargs.get('merchant_id'))
            return cls(merchant, with_agent)

    def __create_url(self, service: str, endpoint: str) -> str:
        return f'{self.__API_URLS.get(service)}{endpoint}'

    @property
    def __auth_credentials(self) -> dict:
        return self.__MERCHANTS.get(self.merchant.value).get('auth_credentials')

    def __send_request(self, payload: Optional[dict], url: str, request_type: str = 'POST') -> dict:
        """
            Отправка запросов к API
            :param url: адрес обращения к апи
            :param payload: json с параметрами запроса
            :param request_type: тип запроса
            :raise: ServiceError
            :return: json ответ от сервиса
        """
        try:
            payload = payload | self.__auth_credentials if payload else self.__auth_credentials
            Logger_lifePay.info(json.dumps(payload))
            if request_type == 'POST':
                response = self.__session.post(url, json=payload)
            elif request_type == 'GET':
                response = self.__session.get(url, params=payload)
            else:
                raise NotImplementedError(f'Метод {request_type} не поддерживается (Возможные варианты GET, POST)')

        except Exception as e:
            raise ServiceError(f'Connection error ({request_type}): {e.__class__.__name__} ({str(e)})')
        response_json = response.json()
        if response.status_code != 200:
            raise ServiceError(f'LifePay service не доступен {response.status_code}')
        elif response_json['code'] != 0:
            raise ServiceError(f'LifePay service  {response_json["code"]}:{response_json["message"]}.\nDetails:'
                               f'{json.dumps(response_json["data"], ensure_ascii=False, indent=2)}')
        return response_json

    def create_recipient(self, payload: dict) -> str:
        """
        Создание чека
        :param payload: Bundle из Services.Sber.Bundle.life_pay_bundle

        :return : uid из ответа
        """
        url = self.__create_url(ServicesType.SAPI.value, 'create-receipt')
        data = self.__send_request(payload, url, 'POST')
        return data.get('data', {}).get('uuid')

    def create_api_refund(self, number: str, **kwargs) -> dict:
        """
        Создание чека возврата

        :param number: Номер чека
        :param kwargs: дополнительные параметры которые могут пригодиться для частичного возврата
            kwargs : {
                uuid : Уникальный идентификатор запроса на возврат.
                items :	Item[] Список позиций на возврат для частичного возврата.
            }
            item : {
                name: Наименование позиции.
                price: Цена за единицу товара
                quantity: Количество товаров в позиции к возврату.
                tax: НДС позиции
            }

        :return: dict словарь с данными об успешном возврате

        """

        url = self.__create_url(ServicesType.SAPI.value, 'transactions/refund')
        payload = {**kwargs, 'number': number}
        data = self.__send_request(payload, url, 'POST')
        return data

    def transaction_list(self, payload: dict = None) -> dict:
        """
        Список чеков (операций)

        :param payload: дополнительные параметры которые могут пригодиться для формирования списка транзакций
        может включать в себя ниже приведенные поля;
            payload: {
                operator: Логин оператора, который совершил транзакцию
                date: Дата транзакции в формате YYYY-MM-DD UTC+0.
                limit: Максимальное количество выводимых записей в диапазоне от 0 до 100. По умолчанию - 10.
                offset : Смещение записей для запроса. По умолчанию - 0.
            }
         :return: возвращает словарь транзакций
        """

        url = self.__create_url(ServicesType.API.value, 'transactions')
        data = self.__send_request(payload, url, 'GET')
        return data


class ReceiptCreator(ABC):
    """
    Интерфейс алгоритмов по созданию чеков
    """

    @abstractmethod
    def create_receipt(self) -> str:
        """
        Создание чека

        :return: Идентификатор созданного чека
        """
        pass

    @property
    @abstractmethod
    def error_message(self) -> str:
        """
        Сообщение об ошибке при формировании чека
        """
        pass

    @property
    @abstractmethod
    def success_message(self) -> str:
        """
        Сообщение об успешном формировании чека
        """
        pass


class ReceiptContext:
    """
    Контекст формирования чека
    """

    def __init__(self,
                 creator: ReceiptCreator = None,
                 logger: Logger = None,
                 log_success: bool = False):
        self._creator = creator
        self.logger = logger
        self.log_success = log_success

    @property
    def creator(self):
        return self._creator

    @creator.setter
    def creator(self, value: ReceiptCreator):
        self._creator = value

    def create_receipt(self) -> Optional[str]:
        """
        Создание чека в заданном контексте

        :return: идентификатор созданного чека
        """
        if not self._creator:
            raise ServiceError('Отсутствует объект ReceiptCreator')

        try:
            receipt = self._creator.create_receipt()
        except Exception as e:
            if self.logger:
                self.logger.error(f'{self._creator.error_message}. {e.__class__.__name__} ({str(e)})')
            return None
        if self.log_success and self.logger:
            self.logger.info(self._creator.success_message)

        return receipt


class PrepaymentSberReceipt(ReceiptCreator):
    """
    Чек аванса при оплате по ссылке
    """

    def __init__(self, lp_srv: Service, /, object_id, amount, order_id, credit_product, refund: bool = False):
        self.srv = lp_srv
        self.credit_product = credit_product
        self.object_id = object_id
        self.order_id = order_id
        self.amount = amount
        self.refund = refund

    @property
    def error_message(self):
        return f"Не удалось сформировать чек по заказу {self.order_id}"

    @property
    def success_message(self):
        return f"Чек по заказу {self.order_id} успешно сформирован"

    def create_receipt(self) -> str:
        with Session(DbName.CORE) as ses:
            franchise_id = ses.query(AmoObjects.franchise_id). \
                filter_by(objects_id=self.object_id). \
                scalar()
            franchise = franchise_data(ses, franchise_id)
            client_info = ses.execute(CLIENT_INFO_BY_OBJECT_ID, {'object_id': self.object_id}).first()
            phone = ''.join([s for s in client_info.phone if s.isnumeric()])

        bundle = Bundle(
            {
                'phone': phone,
                'email': client_info.email,
                'name': client_info.client,
            },
            [
                {
                    'name': f'Аванс по договору {self.object_id}',
                    'price': self.amount,
                    'supplier': {
                        'inn': franchise.inn,
                        'name': franchise.name,
                        'phone': franchise.phone
                    }
                }
            ],
            selected_mto=self.srv.merchant,
            credit_product=self.credit_product,
            order_id=self.order_id,
            bill_type=LifePayOperationType.SELL_REF if self.refund else LifePayOperationType.SELL,
            with_agent=self.srv.with_agent
        )

        receipt_uuid = self.srv.create_recipient(bundle.life_pay_bundle(self.amount))

        return receipt_uuid


class PrepaymentAccountReceipt(ReceiptCreator):
    """
    Чек аванса для реквизитов и СБП
    """

    def __init__(self, lp_srv: Service, /, trs_info):
        self.srv = lp_srv
        self.trs_info = trs_info

    @property
    def error_message(self):
        return f"Не удалось сформировать чек аванса для транзакции {self.trs_info['transaction_id']}"

    @property
    def success_message(self):
        return f"Чек аванса для транзакции {self.trs_info['transaction_id']} успешно сформирован"

    def create_receipt(self) -> str:
        bundle = Bundle(
            {
                'phone': self.trs_info['contact'],
                'name': self.trs_info['client'],
                'email': self.trs_info['client_email']
            },
            [
                {
                    'name': f'Аванс по договору {self.trs_info["object_id"]}',
                    'price': self.trs_info['amount'],
                    'supplier': {
                        'inn': self.trs_info['inn'],
                        'name': self.trs_info['name'],
                        'phone': self.trs_info['phone']
                    }
                }
            ],
            selected_mto=self.srv.merchant,
            order_id=self.trs_info['transaction_id'],
            with_agent=self.srv.with_agent

        )

        receipt_uuid = self.srv.create_recipient(bundle.life_pay_bundle(self.trs_info["amount"]))

        return receipt_uuid

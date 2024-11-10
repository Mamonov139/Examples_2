from collections import namedtuple
from traceback import format_exc
from typing import TypeVar, Optional

from flask import request
from yookassa.domain.common import SecurityHelper
from yookassa.domain.notification import WebhookNotificationFactory
from yookassa.domain.response import PaymentResponse

from Services.common import ServiceFactory, Merchant, ServiceError, uuid
from yookassa import Configuration, Payment
from yookassa.domain.common.user_agent import Version
from Config import configs


SelfService = TypeVar('SelfService', bound="Service")


Webhook = namedtuple("Webhook", ("transaction_id", "event", "merchant"))
Order = namedtuple("Order", ("order_id", "order_url"))


class Service(ServiceFactory):
    """
    Класс, реализующий паттерн фасад для работы с API юкассы
    """

    def __init__(self, merchant: Merchant = Merchant.DOMEO_MART):
        self.merchant = merchant.value
        try:
            merchant = configs['yookassa']['merchants'][self.merchant]
            Configuration.configure(merchant['shop_id'], merchant['secret_key'], framework=Version('Flask', '2.1.2'))
        except KeyError:
            raise ServiceError(f'Merchant {merchant.value} not found in config file')

    @classmethod
    def create_from_user_id(cls, user_id: int, *args, **kwargs) -> Optional[SelfService]:
        """
        :param user_id: идентификатор пользователя

        :return: объект службы Yookassa
        """
        if kwargs.get('merchant_id'):
            merchant = Merchant.find_merchant_by_id(kwargs.get('merchant_id'))
            return cls(merchant)

    def register_order(self, amount: float, description: str, returnUrl: str, transaction_id: str) -> Order:
        """
        Регистрация заказа на площадке

        :param amount: сумма заказа
        :param description: описание заказа
        :param returnUrl: адрес перенаправления
        :param transaction_id: внутриенний идентификатор

        :return: идентификатор созданного заказа, ссылка на оплату
        """

        data = {
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": returnUrl
            },
            "capture": True,
            "description": description,
            "metadata": {
                'transaction_id': transaction_id,
                'merchant': self.merchant
            },
        }

        try:
            payment = Payment.create(data, idempotency_key=uuid())
        except Exception as err:
            raise ServiceError(f"Ошибка создания заказа: {str(err)}\n{format_exc()}")

        return Order(payment["id"], payment['confirmation']['confirmation_url'])

    @staticmethod
    def decline_order(order_id: str):
        """
        Отклонение заказа

        :param order_id: идентификатор заказа в системе yookassa
        :return:
        """
        try:
            _ = Payment.cancel(order_id)
        except Exception as err:
            raise ServiceError(f"Ошибка отмены заказа: {str(err)}\n{format_exc()}")

    @staticmethod
    def get_order(order_id: str) -> dict:
        """
        Получение данных по заказу

        :param order_id: идентификатор заказа в системе yookassa
        :return: объект заказа
        """
        try:
            payment = Payment.find_one(order_id)
        except Exception as err:
            raise ServiceError(f"Ошибка получения заказа: {str(err)}\n{format_exc()}")

        # обратная совместимость с ответом Сбера
        if payment.status == 'pending':
            orderStatus = 0
        elif payment.status == 'canceled':
            orderStatus = 6
        elif payment.status == 'succeeded':
            orderStatus = 2
        else:
            orderStatus = -1

        setattr(payment, "orderStatus", orderStatus)

        return dict(payment)

    @staticmethod
    def prepare_webhook() -> Webhook:
        """
        Подготовка и валидация уведомления о состоянии заказа

        :return: тело уведомления
        """

        ip = request.environ.get("X-Real-IP",
                                 request.environ.get("HTTP_X_FORWARDED_FOR",
                                                     request.environ.get("REMOTE_ADDR",
                                                                         "0.0.0.0")))

        ip = ip.split(",")[0].strip()

        if not SecurityHelper().is_ip_trusted(ip):
            raise ServiceError(f"Неопознанный IP адрес: {ip}", 400)

        try:
            notification_object = WebhookNotificationFactory().create(request.json)
            response_object: PaymentResponse = notification_object.object
        except Exception as err:
            raise ServiceError(f"Ошибка обработки вебхука:  {str(err)}\n{format_exc()}")

        return Webhook(transaction_id=response_object.metadata["transaction_id"],
                       merchant=Merchant.find_merchant(response_object.metadata["merchant"]),
                       event=notification_object.event)

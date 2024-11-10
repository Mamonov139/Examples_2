from flask_restful import reqparse

from API.common import check_entity
from API.parsing_common import check_url, check_payment_method
from DB import DbName, withSession
from DB.models import Transactions

__all__ = ('PaymentsBody', 'PaymentsBase', 'PaymentsLink')


@withSession(DbName.CORE)
def check_transaction(ses, value) -> Transactions:
    transaction = ses.query(Transactions).get(value)

    if not transaction:
        raise ValueError("Транзакция не найдена")

    return transaction


PaymentsBase = reqparse.RequestParser()
PaymentsBase.add_argument('orderId',
                          type=str,
                          required=False,
                          location='args')
PaymentsBase.add_argument('orderNumber',
                          type=str,
                          required=False,
                          location='args')

PaymentsBody = reqparse.RequestParser()
PaymentsBody.add_argument('amount',
                          type=float,
                          required=True,
                          help='Не указана сумма платежа',
                          location='json')
PaymentsBody.add_argument('returnUrl',
                          type=check_url,
                          required=True,
                          help='некорректный URL или сервис недоступен',
                          location='json')
PaymentsBody.add_argument('payment_method',
                          type=check_payment_method,
                          required=True,
                          location='json')
PaymentsBody.add_argument('payment_type',
                          type=str,
                          default='order',
                          help='некорректное значение для логического поля',
                          required=False,
                          location='json')
PaymentsBody.add_argument('entity_id',
                          type=str,
                          required=False,
                          help='Не указан номер акта/объекта',
                          location='json')
PaymentsBody.add_argument('entity_type',
                          type=check_entity,
                          required=False,
                          help='Некорректное значение сущности',
                          location='json')
PaymentsBody.add_argument('merchant_id',
                          type=int,
                          help='идентификатор мерчанта',
                          required=False,
                          location='json')

PaymentsLink = reqparse.RequestParser()
PaymentsLink.add_argument('transaction_id',
                          type=check_transaction,
                          required=True,
                          help='Идентификатор транзакции',
                          location='args',
                          dest="transaction")

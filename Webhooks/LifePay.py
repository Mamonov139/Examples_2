import json

from flask import request, Blueprint
from flask_restful import Resource

from API.common import resp
from DB import withSession, DbName
from DB.models import Transactions
from Logger import get_logger

life_pay_webhooks_bp = Blueprint('life_pay_webhooks_bp', __name__)


class NotificationApi(Resource):
    method_decorators = (withSession(DbName.CORE),)

    def post(self, ses, order_id: str):
        """
        :param ses:
        :param order_id: id транзакции у нас в системе
        :return:
        """
        logger = get_logger('life_pay_webhooks_bp', 'life_pay_webhooks')
        data = request.form.get('data')
        if data:
            transaction = ses.query(Transactions).filter_by(transaction_id=order_id)
            data = json.loads(data)
            if ses.query(transaction.exists()).scalar() and data.get('ofd_url'):
                transaction.update({'receipt': data.get('ofd_url')})
                ses.commit()
            if data.get('error_code'):
                logger.error(f'Чек {data.get("uuid")} не напечатан:\n{json.dumps(data, indent=2, ensure_ascii=False)}')
        else:
            logger.error(f'Не получены от  LifePay  данные по чеку заказа : {order_id}')
        return resp({'message': 'ok'}, 200)

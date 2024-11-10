from datetime import datetime
from traceback import format_exc

from flask import Blueprint
from yookassa.domain.notification import WebhookNotificationEventType

from API.common import resp, is_last_certificate_transaction, set_certificate_status, get_franchise_id_by_object_id, \
    MessageService
from DB import withSession, DbName
from DB.models import getData, Transactions, CertificateVersion, Report, Franchise, AmoObjects, EntityActivity
from Logger import get_logger
from Services.Yookassa import Service as YookassaService, Webhook
from Services.LifePay import Service as LifePayService, ReceiptContext, PrepaymentSberReceipt, FranchiseReceipt
from Services.common import Merchant, PaymentTypes, check_legal, ServiceError, is_nominal_object, FranchiseType, \
    MessageServiceGroupId

Logger = get_logger('webhooks_yookassa', 'webhooks_yookassa')
yookassa_webhooks = Blueprint('yookassa_webhooks', 'yookassa_webhooks')


@yookassa_webhooks.route('/yookassa/callback/<string:merchant>', methods=['POST'])
def yookassa_payments(merchant):
    srv = YookassaService(Merchant.find_merchant(merchant))
    try:
        webhook: Webhook = srv.prepare_webhook()
    except ServiceError as err:
        if err.status_code == 400:
            return resp('Неопознанный IP адрес', 400)
        raise
    try:
        handle_webhook(webhook)
    except Exception as err:
        Logger.error(f"Unhandled webhook: {str(err)}\n{format_exc()}")

    return resp('OK', 200)


@withSession(DbName.CORE)
def handle_webhook(ses, webhook: Webhook):  # noqa: C901:
    """
    Обработка уведомления о статусе платежа

    :param ses: сессия для работыс БД
    :param webhook: атрибуты уведомления
    """
    date_now = getData()
    close_receipt = False

    if webhook.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
        # успешная оплата
        trs: Transactions = ses.query(Transactions).filter_by(transaction_id=webhook.transaction_id).one_or_none()

        if not trs:
            Logger.info(f'Транзакция {webhook.transaction_id} не найдена')
            return

        """
        
        Тут бизнес логика на обработку поступившего веб хука
        
        """

        """

        Тут идет процесс создание чека через LifePay

         """
        lp_srv = LifePayService.create_from_user_id(trs.created_by)

        if not lp_srv:
            Logger.error(f'Невозможно создать службу LifePay для пользователя {trs.created_by}')
            return

        context = ReceiptContext(logger=Logger, log_success=True)
        context.creator = PrepaymentSberReceipt(lp_srv,
                                                object_id=trs.object_id,
                                                amount=trs.amount,
                                                order_id=trs.transaction_id,
                                                credit_product=None)
        context.create_receipt()

    elif webhook.event == WebhookNotificationEventType.PAYMENT_CANCELED:
        pass

    return

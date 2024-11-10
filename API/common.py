from typing import Optional
from datetime import datetime
from traceback import format_exc

from aiohttp import ClientSession
from flask import make_response, jsonify
from requests import post
from sqlalchemy import bindparam as bind, and_
from sqlalchemy.sql import func

from Config import configs
from AuthManager import DepartmentEnum
from DB.models import Franchise, GeneratorOrder, Transactions, CertificateStatus, getData, FranchiseXStatus, \
    AmoObjects, Budgets, Report, ObjectBudget, ParticipantsXObject
from Logger import get_logger

from Services.common import Entity, TransactionTypeCode, PaymentTypes, is_nominal_object, CertificateStatusEnum, \
    FranchiseType



FRANCHISE_DEPARTMENT_ID  = 10
MAX_DATE =  getData(datetime.max)
def resp(data, status):
    return plain_resp(jsonify(data), status, headers=None)


def plain_resp(data, status, headers):
    return make_response(data, status, headers)


def to_dict(t):
    # преобразуем запись из БД в словарь и фильтруем None значения
    return {k: t[k] for k in t.keys() if t[k] is not None}


def get_ssd(ses) -> dict:
    """
    Платёжные данные "ООО "ССД"

    :param ses: сессия sql alchemy
    :return:
    """
    ssd_franchise_id = configs.get('ssd').get('franchise_id')
    ssd = ses.query(Franchise.name,
                    Franchise.inn,
                    Franchise.kpp,
                    Franchise.bank_code,
                    Franchise.account,
                    bind("type", "payment_contract")). \
        filter_by(franchise_id=ssd_franchise_id).one()

    return ssd._asdict()


sber_commission_percent = int(configs.get('commissions').get('sber'))
ssd_commission_percent = int(configs.get('commissions').get('ssd'))
domeo_commission_percent = int(configs.get('commissions').get('domeo'))
sber_commission_coefficient = 1 - sber_commission_percent / 100
ssd_commission_coefficient = 1 - ssd_commission_percent / 100
domeo_commission_coefficient = 1 - domeo_commission_percent / 100


def get_current_user_franchise_id(user):
    if user.from_department(DepartmentEnum.Franchise):
        return user.get_id()
    elif user.from_department(DepartmentEnum.Employee_franchise):
        return user.franchise_id
    else:
        return None


def check_entity(value: str) -> Optional[Entity]:
    if value is None:
        return None
    elif value == Entity.ACT.value:
        return Entity.ACT
    elif value == Entity.OBJECT.value:
        return Entity.OBJECT
    elif value == Entity.ORDER.value:
        return Entity.ORDER
    else:
        raise ValueError()


def get_new_order_id(ses):
    a = GeneratorOrder()
    ses.add(a)
    ses.commit()
    return a.order_id


def is_last_certificate_transaction(ses, certificate_code: str) -> bool:
    """
    Проверка на закрывающий платеж

    :param ses: Сессия sql alchemy.
    :param certificate_code: Идентификатор акта.
    """
    billing_amount = ses.query(Transactions.amount).\
                         filter(Transactions.entity_code == certificate_code,
                                Transactions.payment_type == 'billing',
                                Transactions.is_active.is_(True)).scalar() or 0
    closed_amount = ses.query(func.sum(Transactions.amount)). \
                        filter(Transactions.entity_code == certificate_code,
                               Transactions.transaction_type_code == TransactionTypeCode.CERTIFICATE_PAYMENT.value,
                               Transactions.payment_type.not_in(('billing', 'debt')),
                               Transactions.is_closed.is_(True),
                               Transactions.is_active.is_(True)).scalar() or 0
    return closed_amount == billing_amount


def set_certificate_status(ses, certificate_code: str, transaction_id: str) -> bool:
    """
    Проставляет статус акта в зависимости от поступившего платежа.

    :param ses: Сессия sql alchemy.
    :param certificate_code: Идентификатор акта.
    :param transaction_id: Идентификатор транзакции.
    """
    date_now = getData()
    last_pay = False
    billing_amount = ses.query(Transactions.amount). \
        filter(Transactions.entity_code == certificate_code,
               Transactions.payment_type == 'billing',
               Transactions.is_active.is_(True)).scalar()
    closed_transactions = ses.query(Transactions). \
        filter(Transactions.entity_code == certificate_code,
               Transactions.transaction_type_code == TransactionTypeCode.CERTIFICATE_PAYMENT.value,
               Transactions.payment_type.not_in(('billing', 'debt')),
               Transactions.is_closed.is_(True),
               Transactions.is_active.is_(True)).all()
    closed_amount = sum(ct.amount for ct in closed_transactions)
    identified_amount = sum(ct.amount for ct in closed_transactions if ct.is_identify)
    prepayment_amount = sum(ct.amount for ct in closed_transactions if ct.payment_type == 'prepayment')
    is_last_transaction = closed_amount == billing_amount
    is_first_transaction = closed_transactions and \
                           len([ct for ct in closed_transactions if ct.transaction_id != transaction_id]) == 0
    sq_old_status = ses.query(CertificateStatus). \
        filter_by(certificate_code=certificate_code,
                  date_end=getData(datetime.max))
    old_status = sq_old_status.first()
    new_status_id = None
    if not closed_amount:
        new_status_id = CertificateStatusEnum.READY_TO_PAY.value
    elif is_last_transaction and (closed_amount - prepayment_amount) == identified_amount:
        #TODO убрать амо обжекст добавить budgets и fanchise_id брать из subsidiary в budgets
        franchise_type,participant = ses.query(Franchise.franchise_type,ParticipantsXObject.user_id). \
            select_from(Transactions). \
            join(ParticipantsXObject,and_(
                ParticipantsXObject.object_id == Transactions.object_id,
                ParticipantsXObject.department_id == FRANCHISE_DEPARTMENT_ID,
                ParticipantsXObject.date_end == MAX_DATE),isouter=True).\
            join(AmoObjects, AmoObjects.objects_id == Transactions.object_id). \
            join(Franchise, Franchise.franchise_id == AmoObjects.franchise_id). \
            filter(Transactions.transaction_id == transaction_id).one()

        if franchise_type == FranchiseType.PERFORMER and not participant:
            new_status_id = CertificateStatusEnum.COMPLETED_PAID.value
        else:
            new_status_id = CertificateStatusEnum.IDENTIFIED_PAID
        last_pay = True
    elif is_last_transaction:
        new_status_id = CertificateStatusEnum.UNIDENTIFIED_PAID.value
    elif is_first_transaction or closed_amount:
        new_status_id = CertificateStatusEnum.PARTIALLY_PAID.value
    if new_status_id and (not old_status or old_status.status_id != new_status_id):
        sq_old_status.update({'date_end': date_now})
        ses.add(CertificateStatus(certificate_code=certificate_code,
                                  status_id=new_status_id,
                                  date_start=date_now,
                                  user_id=0))
    if new_status_id in (CertificateStatusEnum.COMPLETED_PAID,
                         CertificateStatusEnum.IDENTIFIED_PAID,
                         CertificateStatusEnum.UNIDENTIFIED_PAID):
        cert_num, budget_id = ses.query(Report.certificate_num, Report.budgets_id). \
            filter(Report.certificate_code == certificate_code).one()
        ses.query(Budgets).filter(Budgets.budgets_id == budget_id).update({'last_paid_cert': cert_num})
    return last_pay


def set_franchisee_status(ses, params):
    date_now = datetime.now()
    max_date = getData(datetime.max)
    ses.query(FranchiseXStatus). \
        filter_by(franchise_id=params.get('franchise_id'), date_end=max_date).update({'date_end': date_now})
    ses.add(FranchiseXStatus(**params))


def get_franchise_id_by_object_id(ses, object_id: int) -> int:
    return ses.query(AmoObjects.franchise_id).filter_by(objects_id=object_id).scalar()


def get_franchise_id_by_cert_code(ses, certificate_code: str) -> int:
    return ses.query(AmoObjects.franchise_id). \
        join(ObjectBudget, ObjectBudget.object_id == AmoObjects.objects_id). \
        join(Report, and_(Report.budgets_id == ObjectBudget.budgets_id,
                          Report.certificate_code == certificate_code)). \
        scalar()


def is_with_agent(ses, object_id: int, certificate_code: str) -> bool:
    is_nominal = is_nominal_object(ses, object_id)

    transactions = ses.query(Transactions).filter_by(object_id=object_id,
                                                     payment_type=PaymentTypes.CASH,
                                                     entity_type=Entity.ACT,
                                                     is_active=True,
                                                     transaction_type_code=TransactionTypeCode.CERTIFICATE_PAYMENT,
                                                     entity_code=certificate_code)
    return is_nominal and not transactions.count()


class MessageService:
    """
    Отправка уведомлений в ТГ через сервис уведомлений Domeo ERP.
    """
    URL = f'{configs.get("ecosystem_address").get("estimate_address")}/tg_msg'
    TOKEN = configs.get('ecosystem_address').get('token')

    logger = get_logger('main', 'ecosystem_cors')

    def send_notification(self, payload):
        try:
            post(self.URL,
                 cookies={'access_token_cookie': self.TOKEN},
                 json=payload)
        except Exception as err:
            self.__log_error(err)

    async def send_async_notification(self, payload, session: ClientSession):
        try:
            async with session.post(self.URL,
                                    cookies={'access_token_cookie': self.TOKEN},
                                    json=payload) as response:
                return response.status
        except Exception as err:
            self.__log_error(err)

    def __log_error(self, err):
        self.logger.error('Не удалось отправить сообщение через внутренний сервис уведомлений',
                          str(err),
                          format_exc())

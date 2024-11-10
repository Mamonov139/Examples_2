from datetime import datetime, timedelta
from enum import Enum
from traceback import format_exc
from typing import Tuple, Optional

from flask_restful import Resource, abort
from AuthManager import WithCurrentUser
from flask import Blueprint, render_template
from sqlalchemy import func

from Config import configs
from API.common import get_franchise_id_by_object_id, resp, plain_resp, get_franchise_id_by_cert_code
from DB import DbName, withSession
from API.parsing_yookassa import *
from DB.models import ObjectBudget, CertificateVersion, Report, AmoObjects, EstimateObjects, Budgets, Clients, \
    Object_x_Client, getData, Transactions
from Logger import get_logger
from Services.common import Entity, uuid, ServiceError, PaymentMethod, TransactionTypeCode, is_nominal_object
from Services.Yookassa import Service as YookassaService

api_services_bp = Blueprint('yookassa_services',
                            __name__,
                            template_folder="yookassa_landings",
                            static_folder="yookassa_landings/static",
                            static_url_path='/yookassa_services/yookassa_landings/static')
Logger = get_logger('yookassa-api', 'yookassa-api')


class YookassaPayments(Resource):
    method_decorators = {
        "get": (withSession(DbName.CORE), WithCurrentUser),
        "post": (withSession(DbName.CORE), WithCurrentUser),
        "delete": (withSession(DbName.CORE),)
    }

    def get(self, ses, current_user):
        """
        получение информации о заказе

        :param ses: сессия для работы с БД
        :param current_user: текущий пользователь
        :return:
        """
        args = PaymentsBase.parse_args()

        merchant_id = None

        if orderId := args.orderId:
            orderNumber = ses.query(Transactions.transaction_id).filter_by(acquiring_order_id=orderId).scalar()
            merchant_id = self._get_order_merchant_id(ses, order_number=orderNumber)
        elif orderNumber := args.orderNumber:
            merchant_id = self._get_order_merchant_id(ses, order_number=orderNumber)
            orderId = ses.query(Transactions.acquiring_order_id).filter_by(transaction_id=orderNumber).scalar()
        else:
            abort(400, message={'message': 'Не указан ни один идентификатор'})

        srv = self._srv(current_user.get_id(), merchant_id=merchant_id)

        data = srv.get_order(orderId)

        return resp(data, 200)

    def post(self, ses, current_user):
        """
        Создать платёж

        :param ses: сессия для работы с БД
        :param current_user: текущий пользователь
        :return:
        """

        now = getData()
        transaction_id = uuid()
        args = PaymentsBody.parse_args()
        order_url = f'{configs.get("domain").get("payment_url")}/order/{transaction_id}'

        # идентификатор франчайзи для новой транзакции
        franchise_id = 0
        if args["entity_type"] == Entity.OBJECT:
            franchise_id = get_franchise_id_by_object_id(ses, args["entity_id"])
        elif args["entity_type"] == Entity.ACT:
            act_code, _ = args['entity_id'].split('_')
            franchise_id = get_franchise_id_by_cert_code(ses, act_code)
        elif args["entity_type"] == Entity.ORDER:
            franchise_id = current_user.get_id()

        # создание новой транзакции
        ses.add(Transactions(transaction_id=transaction_id,
                             payment_type=args.payment_type,
                             transaction_type_code=TransactionTypeCode.PREPAYMENT,
                             document_id=order_url,
                             created_date=now,
                             transaction_date=now,
                             created_by=current_user.get_id(),
                             amount=args['amount'],
                             prepayment_flag=args.payment_method[0] == PaymentMethod.PREPAID,
                             franchise_id=franchise_id))
        ses.commit()

        data = {
            "url": order_url,
            "orderNumber": transaction_id,
            "createdDate": now,
            "message": 'Успешно'
        }

        return resp(data, 201)

    def delete(self, ses):
        """
        деактивация неоплаченного заказа

        :param ses: сессия для работы с БД
        :return:
        """
        args = PaymentsBase.parse_args()
        data = None

        if orderId := args.orderId:
            trs = ses.query(Transactions).filter_by(acquiring_order_id=orderId).one_or_none()
        elif orderNumber := args.orderNumber:
            trs = ses.query(Transactions).filter_by(transaction_id=orderNumber).one_or_none()
        else:
            trs = None
            abort(400, message={'message': 'Не указан ни один идентификатор'})

        if not trs:
            abort(400, message={'message': 'Транзакция не найдена'})
        if trs.is_closed:
            abort(400, message={'message': 'Удалить можно только неоплаченный заказ'})

        trs.is_active = False
        ses.commit()

        return resp(data, 200)

    @staticmethod
    def _get_order_merchant_id(ses, order_number: str) -> Optional[int]:
        """
        Получение идентификатора мерчанта по номеру заказа (идентификатор транзакции)

        :param ses: сессия для работы с БД
        :param order_number: номер заказа
        :return:
        """
        sq = ses.query(EstimateObjects.is_nominal,
                       AmoObjects.franchise_id). \
            select_from(Transactions). \
            filter(Transactions.transaction_id == order_number). \
            join(EstimateObjects, EstimateObjects.object_id == Transactions.object_id). \
            join(AmoObjects, AmoObjects.objects_id == Transactions.object_id).one_or_none()
        if not sq or sq.is_nominal:
            return None
        return sq.franchise_id

    @staticmethod
    def _srv(user_id: int, merchant_id: int = None) -> YookassaService:
        srv = YookassaService.create_from_user_id(user_id, merchant_id=merchant_id)
        if not srv:
            abort(400, message={'message': f'У пользователя {user_id} нет прав на работу с Yookassa'})

        return srv


class YookassaPaymentLinks(Resource):
    method_decorators = (withSession(DbName.CORE),)

    def get(self, ses):
        """
        Формирование и получение ссылки на оплату

        :param ses: сессия для работы с БД
        :return:
        """
        now = datetime.now()

        transaction: Transactions = PaymentsLink.parse_args()["transaction"]

        if not transaction.is_active or transaction.is_closed or now - transaction.created_date > timedelta(days=10):
            abort(400, message={'message': 'Транзакция не активна или уже оплачена'})

        description, merchant_id = self._get_desc_and_merchant(ses, transaction.entity_type, transaction.entity_code)

        srv = YookassaService.create_from_user_id(transaction.created_by, merchant_id=merchant_id)

        try:
            order = srv.register_order(transaction.amount, description, "https://domeo.ru/", transaction.transaction_id)
        except ServiceError as err:
            Logger.error(f'Не удалось зарегестрировать заказ: {str(err)}\n{format_exc()}')
            return resp('Ошибка при регистрации заказа', 500)

        ses.query(Transactions). \
            filter_by(transaction_id=transaction.transaction_id). \
            update({"order_url": order.order_url, "acquiring_order_id": order.order_id})
        ses.commit()

        return resp({"url": order.order_url, "message": 'Успешно'}, 201)

    @staticmethod
    def _get_desc_and_merchant(ses, entity_type, entity_id) -> Tuple[str, int]:
        """
        Метод формирования описания по входным данным платежа, а так же поиска мерчанта объекта

        :param ses: сессия для работы с БД
        :param entity_type: тип сущности - акт или объект
        :param entity_id: идентификатор сущности
        :return:
        """
        merchant_id = None
        if entity_type == Entity.ACT:
            # оплата за акт
            res = ses.query(ObjectBudget.object_id,
                            func.to_char(CertificateVersion.updated_date, "DD.MM.YYYY").label("cert_date"),
                            Report.certificate_num,
                            AmoObjects.franchise_id,
                            EstimateObjects.is_nominal,
                            func.to_char(Budgets.contract_date, "DD.MM.YYYY").label("contract_date"),
                            func.concat(Clients.second_name, ' ',
                                        Clients.first_name, ' ',
                                        Clients.middle_name).label("fio")). \
                join(Report, ObjectBudget.budgets_id == Report.budgets_id). \
                join(Budgets, Budgets.budgets_id == Report.budgets_id). \
                join(CertificateVersion, CertificateVersion.certificate_code == Report.certificate_code). \
                join(Object_x_Client, Object_x_Client.object_id == ObjectBudget.object_id, isouter=True). \
                join(Clients, Clients.client_id == Object_x_Client.client_id, isouter=True). \
                join(AmoObjects, AmoObjects.objects_id == ObjectBudget.object_id, isouter=True). \
                join(EstimateObjects, EstimateObjects.object_id == ObjectBudget.object_id). \
                filter(Report.certificate_code == entity_id). \
                one_or_none()

            if not res.is_nominal:
                merchant_id = res.franchise_id
                if not merchant_id:
                    abort(400, message={'message': f'На объекте {res.object_id} не установлен мерчант'})
                    Logger.warning(f'На объекте {res.object_id} не установлен мерчант')

            contract_num = res.object_id

            description = f'Оплата Акта №{res.certificate_num} от {res.cert_date} по договору ' \
                          f'{contract_num} от {res.contract_date}, {res.fio}'

        elif entity_type == Entity.OBJECT:
            # оплата аванса по договору
            if not is_nominal_object(ses, object_id=entity_id):
                merchant_id = get_franchise_id_by_object_id(ses, entity_id)
                if not merchant_id:
                    abort(400, message={'message': f'На объекте {entity_id} не установлен мерчант'})
                    Logger.warning(f'На объекте {entity_id} не установлен мерчант')

            description = f'Аванс по договору {entity_id}'
        elif entity_type == Entity.ORDER:
            # оплата за заказ
            description = 'Оплата за ремонтно-отделочные работы'
        else:
            description = 'Оплата за ремонтно-отделочные работы'

        return description, merchant_id


class YookassaPaymentLending(Resource):
    method_decorators = (withSession(DbName.CORE),)

    class States(str, Enum):
        READY_FOR_PAY = "ready_for_pay"
        LINK_DEAD = "link_dead"
        ALREADY_PAYED = "already_paid"

    def get(self, ses, transaction_id):
        """
        Получение лендинг-страниц для оплаты и проверки статуса платежа

        :param ses: сессия для работы с БД
        :param transaction_id: идентификатор транзакции
        :return:
        """
        now = datetime.now()
        data = {}
        transaction: Transactions = ses.query(Transactions).get(transaction_id)
        order = transaction.entity_code
        is_act = transaction.transaction_type_code == TransactionTypeCode.CERTIFICATE_PAYMENT
        if is_act:
            # если транзакция за акт, то order это код акта, а нам нужен порядковый номер
            order = ses.query(Report.certificate_num).filter_by(certificate_code=order).scalar()
        if not transaction.is_active:
            # заказ недействителен
            state = self.States.LINK_DEAD
        elif transaction.is_closed:
            # заказ уже оплачен
            state = self.States.ALREADY_PAYED
            data["title"] = f"акт № {order}" if is_act else f"аванс по договору {order}"
        elif now - transaction.created_date > timedelta(days=10):
            # срок жизни заказа истёк
            state = self.States.LINK_DEAD
            transaction.is_active = False
            ses.commit()
        else:
            # заказ готов к оплате
            state = self.States.READY_FOR_PAY
            data["title"] = f"акта № {order}" if is_act else f"аванса по договору № {order}"
            data["amount"] = transaction.amount

        return plain_resp(render_template("payment_landing.html", state=state, data=data),
                          200,
                          {'Content-Type': 'text/html; charset=utf-8'})

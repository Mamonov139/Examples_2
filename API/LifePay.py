from flask import Blueprint
from flask_restful import Resource, abort

from API.common import resp, get_franchise_id_by_object_id, is_with_agent
from API.parsing_life_pay import *
from DB import withSession, DbName, rawRequest
from Logger import get_logger

from Services import LifePayService
from Services.LifePay import ReceiptContext, FranchiseReceipt, ContractorReceipt, NotNominalReceipt
from MainApp import WithCurrentUser
from Services.common import check_legal, is_nominal_object

api_services_bp = Blueprint('life_pay_service', __name__)


class LifePayBills(Resource):
    method_decorators = (withSession(DbName.CORE), WithCurrentUser,)

    PARSERS = {
        'franchise': lp_franchise_args,
        'foreman': lp_foreman_args,
        'contractor': lp_contractor_args,
        'foreman_cash_prepayment': lp_foreman_cash_prepayment_args,
    }

    @staticmethod
    def __get_franchise(current_user):
        return current_user.franchise_id or current_user.get_id()

    def post(self, ses, current_user, category: str = 'franchise'):  # noqa: C901:
        logger = get_logger('lp_receipts', 'lp_receipts')
        merchant_id = None

        if not self.PARSERS.get(category):
            abort(404, message={f"Невозможно создать чек для {category}"})

        kwargs = self.PARSERS.get(category).parse_args()

        if check_legal(ses, kwargs.object_id):
            return abort(409, message={f"Невозможно создать чек для {category}"})
        if category in ('franchise', 'foreman', 'foreman_cash_prepayment'):
            object_id = kwargs.get('object_id')
            if not is_nominal_object(ses, object_id):
                merchant_id = get_franchise_id_by_object_id(ses, object_id)
        with_agent = True

        if category in ('foreman', 'foreman_cash_prepayment', 'franchise'):
            if kwargs.certificate_code:
                with_agent = is_with_agent(ses, object_id=kwargs.object_id,
                                           certificate_code=kwargs.certificate_code)
            elif kwargs.is_prepayment:
                with_agent = False

        lp_srv = LifePayService.create_from_user_id(current_user.get_id(),
                                                    merchant_id=merchant_id,
                                                    with_agent=with_agent)
        if not lp_srv:
            abort(400,
                  message={'message': f'У пользователя {current_user.get_id()} нет необходимых прав на создание чеков'})

        franchise_id = kwargs.franchise_id or self.__get_franchise(current_user)

        context = ReceiptContext(logger=logger, log_success=True)
        if category == 'franchise':
            # чек в рамках франшизы МБР
            kwargs["franchise_id"] = franchise_id
            creator = FranchiseReceipt(lp_srv, **kwargs)
        elif category == 'foreman':
            creator = FranchiseReceipt(lp_srv, **kwargs)
        elif category == 'contractor':
            # чек в рамках поставщиков
            kwargs["franchise_id"] = franchise_id
            creator = ContractorReceipt(lp_srv, **kwargs)
        elif category == 'foreman_cash_prepayment':
            transaction = ses.execute(rawRequest.GET_TRANSACTION_FOR_BILL,
                                      {'transaction_id': kwargs['transaction_id']}).fetchone()
            creator = NotNominalReceipt(lp_srv,
                                        object_id=kwargs['object_id'],
                                        amount=transaction.amount,
                                        order_id=kwargs['transaction_id'],
                                        email=transaction.client_email,
                                        phone=transaction.client_phone,
                                        client_name=transaction.client_name,
                                        merchant_id=merchant_id,
                                        is_cash=True)
        else:
            return resp({"message": f"Невозможно создать чек для {category}"}, 404)

        context.creator = creator
        receipt_uuid = context.create_receipt()
        if not receipt_uuid:
            return resp({"message": "Не удалось сформировать чек"}, 500)

        return resp({"message": "Чек успешно создан", "receipt": receipt_uuid}, 201)

from flask_restful import reqparse

__all__ = ('lp_franchise_args',
           'lp_contractor_args',
           'lp_foreman_cash_prepayment_args',
           'lp_foreman_args')

lp_base_args = reqparse.RequestParser()
lp_base_args.add_argument('object_id',
                          type=int,
                          required=True,
                          help='Недопустимое значение или аргумент отсутствует',
                          location='json')
lp_base_args.add_argument('certificate_code',
                          type=str,
                          help='Некорректный certificate_code',
                          location='json')

lp_franchise_args = lp_base_args.copy()

lp_franchise_args.add_argument('franchise_id',
                               type=int,
                               location='json',
                               help='Недопустимое значение или аргумент отсутствует')
lp_contractor_args = reqparse.RequestParser()
lp_contractor_args.add_argument('order_id',
                                type=str,
                                required=True,
                                help='Недопустимое значение или аргумент отсутствует',
                                location='json')

lp_foreman_args = lp_base_args.copy()

lp_foreman_args.add_argument('franchise_id',
                             type=int,
                             required=True,
                             location='json',
                             help='Недопустимое значение или аргумент отсутствует')

lp_foreman_cash_prepayment_args = lp_franchise_args.copy()
lp_foreman_cash_prepayment_args.add_argument('transaction_id',
                                             type=str,
                                             required=True,
                                             location='json',
                                             help='Недопустимое значение или аргумент отсутствует')
lp_foreman_cash_prepayment_args.add_argument('is_prepayment',
                                             type=bool,
                                             location='json',
                                             help='Недопустимое значение')

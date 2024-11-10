from flask_restful import Api
from API.LifePay import api_services_bp as api_services_life_pay_bp, LifePayBills
from API.Yookassa import api_services_bp as api_services_yookassa_bp, YookassaPayments, YookassaPaymentLinks


Version = 'v1'  # версия API
api_services_life_pay = Api(api_services_life_pay_bp)
api_services_yookassa = Api(api_services_yookassa_bp)

# регистрация ресурса API LIFEPAY
api_services_life_pay.add_resource(LifePayBills, f'/services/api/{Version}/LifePay/receipts/<string:category>')
# новый эквайринг Yookassa
api_services_yookassa.add_resource(YookassaPayments, f'/services/api/{Version}/yookassa/payments')
api_services_yookassa.add_resource(YookassaPaymentLinks, f'/services/api/{Version}/yookassa/payment_link')


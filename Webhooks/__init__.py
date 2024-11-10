from flask_restful import Api

from Webhooks.Yookassa import yookassa_webhooks as yookassa_webhooks_bp
from Webhooks.LifePay import life_pay_webhooks_bp, NotificationApi


api_webhooks_life_pay = Api(life_pay_webhooks_bp)

__all__ = ( life_pay_webhooks_bp, yookassa_webhooks_bp)

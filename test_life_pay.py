# from uuid import uuid4

from Services import LifePayService
from Services.Sber import Bundle
from Services.common import Merchant, LifePayOperationType, PaymentMethod, PaymentObject  # , CreditProduct

customer_params = {
    'name': 'Клюев Никита Сергеевич',
    'phone': '+79169652516',
    'inn': '',
    'email': 'kai@it.domeo.ru'
}
item_list = [{
    'name': 'Акт номер 2 по договору',
    'price': 3333.00,
    'amount': 1,
    'supplier': {
        'phone': '79645651675',
        'name': 'ДомеоМаркетинг',
        'inn': '7743013901',
    },
    'payment_method': PaymentMethod.PAYMENT,
    'payment_object': PaymentObject.PAYMENT
}]

if __name__ == '__main__':
    ext_id = 'bd795a54-943f-41eb-8b86-7db7c7ab14cc'

    # data = Bundle(customer_params,
    #               item_list,
    #               bill_type=LifePayOperationType.SELL_REF,
    #               bill_uid='a1bb06ab-2697-4921-8e1f-95304fae656f').\
    #     life_pay_bundle(22.13)
    # data = Bundle(
    #     customer_params, item_list, credit_product=CreditProduct.CREDIT,
    #     bill_type=LifePayOperationType.SELL).life_pay_bundle(5000.13)
    data = Bundle(
        customer_params, item_list, bill_type=LifePayOperationType.SELL, order_id=ext_id, prepayment_amount=3000
    ).life_pay_bundle(3333.00)

    life_pay_integration = LifePayService(Merchant.DOMEO_MART)
    # r = life_pay_integration.transaction_list()
    resp = life_pay_integration.create_recipient(data)
    r = resp

import re
from datetime import datetime

from functools import reduce

import requests

from Services.common import PaymentMethod, PaymentObject, TransactionTypeCode


user_agent_val = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)' \
                 ' Chrome/92.0.4515.159 Safari/537.36'


def check_inn(value: str):
    """
    Валидация ИНН

    :param value: строка ИНН
    :return: ИНН
    :raise: ValueError
    """
    inn = tuple(int(i) for i in value)
    len_inn = len(inn)
    if len_inn == 10:
        check_val = inn_check_val(inn, (2, 4, 10, 3, 5, 9, 4, 6, 8, 0))
        if check_val != inn[-1]:
            raise ValueError('ИНН не прошёл проверку на валидность')
    elif len_inn == 12:
        check_val1 = inn_check_val(inn, (7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0))
        check_val2 = inn_check_val(inn, (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0))
        if check_val1 != inn[-2] or check_val2 != inn[-1]:
            raise ValueError('ИНН не прошёл проверку на валидность')
    else:
        raise ValueError('ИНН не прошёл проверку по длине')

    return value


def inn_check_val(inn: tuple, coefficients: tuple) -> int:
    """
    Рассчёт контрольного числа ИНН

    :param inn: элементы ИНН
    :param coefficients: коэффициенты рассчёта
    :return: контрольное число ИНН
    """
    check_sum = reduce(lambda conv, val: conv + val[0] * val[1], zip(inn, coefficients), 0)
    check_val = check_sum % 11
    if check_val > 9:
        check_val = check_val % 10

    return check_val


def check_phone(value: str):
    if not re.match(r'^((\+7|7|8)?([0-9]){10})', value):
        raise ValueError('Номер телефона не соответствует требуемому формату')

    return value


def check_bool(value: str):
    if isinstance(value, bool):
        return value
    if value == 'true':
        return True
    if value == 'false':
        return False

    raise ValueError()


def check_payment_method(value: str) -> tuple:
    if value == 'prepaid':
        return PaymentMethod.PREPAID, PaymentObject.PAYMENT
    elif value == 'payment':
        return PaymentMethod.PAYMENT, PaymentObject.WORK

    raise ValueError()


def check_transaction_type_code(value: str) -> str:
    if value == TransactionTypeCode.PREPAYMENT.value:
        return value
    elif value == TransactionTypeCode.CERTIFICATE_PAYMENT.value:
        return value
    elif value == TransactionTypeCode.CONTRACTOR_OFFER.value:
        return value
    raise ValueError()


def check_date(return_datetime: bool = False):
    def checker(value: str):
        new_value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return new_value if return_datetime else value

    return checker


def check_url(value: str):
    try:
        r = requests.head(value, headers={'User-Agent': user_agent_val})
        if r.status_code > 399:
            raise ConnectionError(f'В ответе код ошибки {r.status_code}: {r.text}')
    except Exception as e:
        raise ValueError(f'URL не прошёл проверку: {str(e)}')

    return value

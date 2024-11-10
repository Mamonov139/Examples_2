# -*- coding: utf-8 -*-
"""
    Estimate.responses.py
    -----------
    Служебные ответы контроллеров сохранения

    :copyright: (c) 2021 by Mark Tolubaev
"""
from flask import jsonify, make_response


# ----------------------------------------------------------------------------------------------------------------------
#                                                       errors
# ----------------------------------------------------------------------------------------------------------------------

def resp_400(data):
    return make_response(jsonify(data), 400)


def missing_arguments_400(reporter, *args):
    data = {'from': reporter,
            'message': f'В запросе отсутствует обязательные параметр: {" ".join(args)}'}
    return make_response(jsonify(data), 400)


def missing_data_parts_400(reporter, *args):
    data = {'from': reporter,
            'message': 'В теле запроса или во вложенных структурах (JSON) '
                       f'отсутствуют обязательные поля: {" ".join(args)}'}
    return make_response(jsonify(data), 400)


def forbidden_403(reporter, resource):
    data = {'from': reporter,
            'message': f'У текущего пользователя нет доступа к ресурсу: {resource}'}
    return make_response(jsonify(data), 403)


def incorrect_args_400(reporter, text):
    data = {'from': reporter,
            'message': f'Некорректные данные: {text}'}
    return make_response(jsonify(data), 400)


def information_not_found_404(reporter, text):
    data = {'from': reporter,
            'message': f'Запрошенная информация не найдена. {text}'}
    return make_response(jsonify(data), 404)


def method_not_allowed_405(reporter):
    data = {'from': reporter,
            'message': 'Данный метод не доступен для запрашиваемого ресурса'}
    return make_response(jsonify(data), 405)


def db_error_500(reporter, original):
    data = {'from': reporter,
            'message': 'Возникла ошибка при работе с базой данных. Оригинал ошибки в блоке exception',
            'exception': original}
    return make_response(jsonify(data), 500)


def error_500(reporter, message, original):
    data = {'from': reporter,
            'message': message,
            'exception': original}
    return make_response(jsonify(data), 500)


def not_authorized(url):
    return make_response(jsonify(url), 401)


# ----------------------------------------------------------------------------------------------------------------------
#                                                      success
# ----------------------------------------------------------------------------------------------------------------------

def ok_200(reporter, message, payload=None):
    data = {'from': reporter,
            'message': message}
    if payload:
        data.update({'payload': payload})
    return make_response(jsonify(data), 200)


def created_201(reporter, resource_data, message="Ресурс создан"):
    data = {'from': reporter,
            'message': message,
            'resource': resource_data}
    return make_response(jsonify(data), 201)

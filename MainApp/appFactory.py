from time import sleep
from os import path
from flask import Flask
from flask_cors import CORS
from swagger_ui import api_doc
from AuthManager import AuthManager

from API.common import resp
from MainApp import clear_cache
from TelegramBot.dialog import bot

from Config import configs


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = configs.get('flask').get('secret')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['JSON_AS_ASCII'] = False

    CORS(app,
         resourses={r"services/api*": {"origin": configs.get('cors').get('origins').split(';')}},
         supports_credentials=True)

    # ------------------------------------------------------------------------------------------------------------------
    #                                               Blueprints registration
    # ------------------------------------------------------------------------------------------------------------------

    from Webhooks import yookassa_webhooks_bp
    app.register_blueprint(yookassa_webhooks_bp)

    from Webhooks import life_pay_webhooks_bp
    app.register_blueprint(life_pay_webhooks_bp)

    from API import api_services_yookassa_bp
    app.register_blueprint(api_services_yookassa_bp)

    bot_token = configs.get('telegram_bot_trans').get('token')
    url_bot = f'/bot/{bot_token}'
    if bot_token:
        base_address = configs.get('telegram_bot_trans').get('base_proxy_notify_address')
        # bot.remove_webhook()
        # sleep(1)
        # _ = bot.set_webhook(url=f'{base_address}/{bot_token}')
    clear_cache()
    # белый список адресов без аутентификации
    white_url_list = ('static', '/sber/callback/', url_bot, '/bot/responder',
                      '/lifepay/callback/', '/mandarin/callback/', '/api/doc',
                      '/api/doc/editor', '/yookassa/callback/', '/order/',
                      '/yookassa/payment_link')
    external_url_list = ('/waybills/rough', )
    # список правил для API адресов
    api_url_rules = ('/services/api/',)
    auth_manager = AuthManager(white_url_list=white_url_list,
                               api_url_rules=api_url_rules,
                               external_url_list=external_url_list)
    auth_manager.register_app(app)
    auth_manager.config['AUTH_URL'] = configs.get("auth").get("url")
    auth_manager.config['REDIRECT_DOMAIN'] = configs.get('domain').get('url')

    # подключаем файл с документацией
    config_path = path.join(path.dirname(path.abspath(__file__)), 'swagger.yaml')
    api_doc(app,
            config_path=config_path,
            url_prefix="/api/doc",
            title="swagger",
            editor=True)

    @app.route("/sitemap")
    def sitemap_endpoint():
        # контроллер со списком конечных точек
        number = 0
        sitemap = [{"methods": ', '.join(m for m in r.methods if m not in ('OPTIONS', 'HEAD')),
                    "rule": r.rule,
                    "endpoint": r.endpoint,
                    "number": (number := number + 1)} for r in app.url_map.iter_rules() if bot_token not in r.rule]

        return resp(sitemap, 200)

    return app

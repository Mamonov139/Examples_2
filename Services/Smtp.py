import os
import smtplib
import ssl
import certifi

from jinja2 import FileSystemLoader

from jinja2.environment import Environment
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from Config import configs
from .common import ServiceError


class Service:
    def __init__(self):
        self.__templatesDirectory = os.path.join(os.path.dirname(__file__), r'templates')

    def send_payment(self, data: dict, to: str):
        try:
            self.__sendEmail("payment.html", data, to)
        except Exception as e:
            raise ServiceError(f'Не удалось отправить письмо: {e.__class__.__name__}({str(e)}')

    def __sendEmail(self, template, data: dict, toEmail: str) -> int:
        HOST = configs.get('smtp_client').get('HOST')
        PORT = configs.get('smtp_client').get('PORT')
        FROM = configs.get('smtp_client').get('FROM')
        username = configs.get('smtp_client').get('username')
        password = configs.get('smtp_client').get('password')

        emailContent = self.__renderTemplate(template, data=data)

        message = MIMEMultipart("Alternative")
        message["Subject"] = "Payments"
        message["From"] = FROM
        message["To"] = toEmail
        message.attach(MIMEText(emailContent, "html"))

        context = ssl.create_default_context(cafile=certifi.where())
        with smtplib.SMTP_SSL(HOST, PORT, context=context) as server:
            # server.set_debuglevel(1)
            responseCode, _ = server.ehlo(HOST)
            if responseCode == 250:
                server.login(username, password)
                server.sendmail(FROM, toEmail, message.as_string())
                return 0
        return -1

    def __renderTemplate(self, template: str, data: dict = None):
        env = Environment()
        env.loader = FileSystemLoader(self.__templatesDirectory)
        _template = env.get_template(template)
        return _template.render(data=data)

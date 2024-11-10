import sentry_sdk
from celery import Celery, signals
from sentry_sdk.integrations.celery import CeleryIntegration

from Config import configs

app = Celery('MainApp')


@signals.celeryd_init.connect
def init_sentry(**_kwargs):
    if env := configs.get("sentry").get("env"):
        sentry_sdk.init(
            dsn=configs.get("sentry").get("dsn"),
            environment=env,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            debug=True,
            integrations=[
                CeleryIntegration(monitor_beat_tasks=True)
            ]
        )


app.config_from_object('MainApp.celery_config')
app.autodiscover_tasks()


app.conf.beat_schedule = {
   'check_email_acquiring': {
        'task': 'API.tasks.get_acquiring_reports_task',
        'schedule': 10800,  # каждые 3 часа
        'args': tuple(),
    },
}

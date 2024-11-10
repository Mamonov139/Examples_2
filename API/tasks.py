from MainApp.celery import app
from Services.SberAcquiring import FactoryReport
from TelegramBot.webHooks import reportError, crossReportSber

from Logger import get_logger
from Services import LifePayService, ServiceError

from Services.common import ReportGroup


Logger = get_logger('tochka-api-tasks', 'tochka-api-tasks')


# ----------------------------------------------------------------------------------------------------------------------
#                                               Асинхронные задачи
# ----------------------------------------------------------------------------------------------------------------------


@app.task(autoretry_for=(ServiceError,), max_retries=2)
def get_acquiring_reports_task():
    """
    Периодический опрос почты на наличие отчётов эквайринга
    """
    try:
        reports = []
        for creditor in ReportGroup:
            au = FactoryReport.create_report_service(creditor.value)
            report = au.get_acquiring_reports()
            reports.extend(report)
        if reports:
            for report_id in reports:
                crossReportSber(report_id=report_id)
    except Exception as e:
        reportError()
        Logger.error(f'Не удалось получить отчёты с почты: {e.__class__.__name__} ({str(e)})')
        raise


import logging
import os.path

from logging.handlers import TimedRotatingFileHandler

from Config import configs


ff = logging.Formatter(fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def get_logger(name: str, file_name: str, level: int = logging.INFO):
    """
    Функция формирует объект логировщика для записи данных о работе приложения в файл

    :param name: имя логировщика
    :param file_name: имя файла, в который будут записываться логи
    :param level: уровень записи информации
    :return: объект логировщика
    """
    fh = TimedRotatingFileHandler(os.path.join(configs.get("logs").get("path"), file_name),
                                  when='D',
                                  interval=1,
                                  backupCount=30,
                                  encoding='utf-8',
                                  delay=True)
    fh.setLevel(level)
    fh.setFormatter(ff)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(fh)

    return logger

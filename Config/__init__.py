from yaml import load, Loader
import os


config_file = 'config.yaml'

cp = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(cp, config_file), 'r', encoding='utf-8') as f:
        configs = load(f, Loader)
except FileNotFoundError:
    raise FileNotFoundError(f'Конфигурационный файл {os.path.join(cp, config_file)} не найден системой')

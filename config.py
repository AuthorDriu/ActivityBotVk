from os import getenv

from dotenv import load_dotenv


load_dotenv(".env")


# Настройки бота будут храниться в объекте класса Config
# Создавать объект самостоятельно не нужно, так как он создаётся
# При импортировании config.py.
# Желательно использовать импорт именно объекта класса из модуля,
# А не самого модуля. То есть так: 
#     from config import bot_config 
#
# А не так:
#     import config

class Config:
    access_token = getenv("ACCESS_TOKEN")
    results_time = getenv("RESULTS_TIME")
    report_access = list(map(int, getenv("REPORT_ACCESS").split()))


bot_config = Config()
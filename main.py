import logging

logging.basicConfig(filename="ActivityBotVK.log", level=logging.INFO)
logger = logging.getLogger(__name__)

from typing import Optional

import datetime
import database as db

import json

from tempfile import NamedTemporaryFile

import vk_api
from vk_api.upload import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType

import schedule

from schemas import Role, User, Activity
from config import bot_config
from report import generate_xl
from upload import upload_file_from_bytes


def start_timer_activity(user_id: int):
    """Запускает таймер для пользователя"""
    user = db.get_user_by_vk_id(user_id)
    
    if not user:
        return "Пользователя нет в базе данных"
    
    if user.state == 1:
        return "Пользователь активен в данный момент"
    
    user.state = db.ActivityType.START
    activity = create_activity(user, db.ActivityType.START)
    
    db.update_user(user)
    db.add_activity(activity)
    
    return "Таймер запущен"


def stop_timer_activity(user_id: int):
    """Останавливает таймер для пользователя"""
    user = db.get_user_by_vk_id(user_id)
    
    if not user:
        return "Пользователя нет в базе данных"
    
    if user.state == 0:
        return "Пользователь не активен в данный момент"

    user.state = db.ActivityType.STOP
    activity = create_activity(user, db.ActivityType.STOP)
    
    db.update_user(user)
    db.add_activity(activity)
    
    return "Таймер остановлен"


def get_timer(user_id: int):
    user = db.get_user_by_vk_id(user_id)
    
    if not user:
        return "Пользователя нет в базе данных"
    
    active_time = calculate_results_for_user(user, current_date())
    
    return f"Ваш статус: {'активен' if user.state == 1 else 'не активен'}\n" \
           f"Вы были активны: {datetime.datetime.utcfromtimestamp(active_time).strftime('%H:%M:%S')}\n" \
           f"Осталось: {datetime.datetime.utcfromtimestamp(max(0, user.role.daily_norm - active_time)).strftime('%H:%M:%S')}"


def get_results(date: str) -> Optional[bytes]:
    """Возвращает документ Excel с результатами за дату"""
    results = db.get_results_by_date(date)
    
    if len(results) == 0:
        return None
    
    report = generate_xl(results, date)
    return report
    

def calculate_results_for_user(user: User, date: str, finish=False) -> int:
    activities = db.get_activities_by_user(user, date)
    
    active_time = 0
    
    for i in range(0, len(activities) - 1 if len(activities) % 2 != 0 else len(activities), 2):
        active_time += activities[i + 1].time_utc - activities[i].time_utc
        
    if len(activities) % 2 != 0:
        if finish:
            user.state = db.ActivityType.STOP
            db.update_user(user)
            db.add_activity(create_activity(user, db.ActivityType.STOP))
        
        active_time += utc_now() - activities[-1].time_utc
        
    return active_time


def create_activity(user: User, _type: db.ActivityType) -> Activity:
    date = current_date()
    now = utc_now()
    
    activity = Activity(
        user=user,
        date=date,
        time_utc=now,
        type=_type
    )
    
    return activity


def utc_now() -> int:
    return round(datetime.datetime.timestamp(datetime.datetime.now(datetime.UTC)))


def current_date(sep=".") -> str:
    date = datetime.date.today()
    return f"{date.day}{sep}{date.month}{sep}{date.year}"


def send_message(vk, user_id, message):
    vk.messages.send(user_id=user_id, random_id=0, message=message)


def send_help(vk, user_id):
    send_message(vk, user_id, 
                """Команды:
                start - запустить таймер
                stop - остановить таймер
                time - посмотреть оставшееся время""")


def main():
    session = vk_api.VkApi(token=bot_config.access_token)
    vk = session.get_api()
    longpoll = VkLongPoll(session)
    
    logger.info("Бот начинает свою работу")
    print("Бот запущен")
    
    for event in longpoll.listen():
        if event.type != VkEventType.MESSAGE_NEW or not event.to_me:
            continue
        
        user_id = event.user_id
        text = event.text.lower()
        
        logger.debug(f"[{user_id}]: {text}")
        
        if text == "start":
            send_message(vk, user_id, start_timer_activity(user_id))
        elif text == "stop":
            send_message(vk, user_id, stop_timer_activity(user_id))
        elif text == "time":
            send_message(vk, user_id, get_timer(user_id))
            
        elif text.startswith("report"):
            if user_id not in bot_config.report_access:
                send_help(vk, user_id)
                continue
            
            arguments = text.split()
    
            if len(arguments) == 1:
                date = current_date()
            else:
                date = arguments[1]
            
            report = get_results(date)
            
            if not report:
                send_message(vk, user_id, f"Результатов за {date} нет")
                continue
            
            url = upload_file_from_bytes(report, f"{current_date('_')}_report.xls")
            
            if not url:
                send_message(vk, user_id, "Не удалось выгрузить результаты... Простите...")
                continue
            else:
                send_message(vk, user_id, f"Результаты за {date}:\n{url}")    
            
        else:
            send_help(vk, user_id)            


if __name__ == "__main__":
    main()

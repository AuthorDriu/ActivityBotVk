from typing import List
import time
import logging
import schedule

import vk_api

from main import current_date, calculate_results_for_user
from config import bot_config
import database as db
from schemas import Result
from report import generate_xl
from upload import upload_file_from_bytes

logger = logging.getLogger(__name__)

print(f"Каждый день в {bot_config.results_time} будут подводиться итоги")


# Должна вызываться самостоятельно раз в день для подведения итогов
def summarize_results(date) -> List[Result]:   
    vk_ids = map(lambda vk_id: vk_id[0], db.get_all_vk_ids())
    users = list(map(db.get_user_by_vk_id, vk_ids))
    results = []

    for user in users:
        _current_date = date
        active_time = calculate_results_for_user(user, _current_date, finish=True)
        difference = user.role.daily_norm - active_time
        result = Result(
            user=user,
            date=_current_date,
            active_time_utc=active_time,
            difference_utc=difference
        )
        results.append(result)

    return results
    
    
def send_results(user_id_list: List[int], url: str):
    session = vk_api.VkApi(token=bot_config.access_token)
    vk = session.get_api()
    
    for user_id in user_id_list:
        vk.messages.send(user_id=user_id, random_id=0, message=f"Плановый отчёт:\n{url}")


def main():
    date = current_date()
    results = summarize_results(date)
    
    for result in results:
        db.add_result(result)
        
    report = generate_xl(results, date)
    
    if not report:
        logger.error("Не удалось сформировать отчёт")
        return
    
    url = upload_file_from_bytes(report, f"плановый_отчёт.xls")
    
    if not url:
        logger.error("Не удалось выгрузить отчёт")
        return
    
    send_results(bot_config.report_access, url)
    

schedule.every().day.at(bot_config.results_time).do(main)


while True:
    schedule.run_pending()
    time.sleep(1)

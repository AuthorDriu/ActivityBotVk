import os
import sqlite3
import logging

from enum import Enum
from pathlib import Path
from typing import Optional, List

from schemas import Role, User, Activity, Result


logger = logging.getLogger(__name__)


# Создание базы данных, если таковой нет

PATH_TO_DATABASE = Path(os.path.abspath(__file__)).parent / "database.sqlite3"

con = sqlite3.connect(PATH_TO_DATABASE)


# Подготовка БД к работе

con.execute("""CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT NOT NULL UNIQUE,
                daily_norm INTEGER NOT NULL
            );""")

con.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                role TEXT NOT NULL,
                state INTEGER NOT NULL,
                FOREIGN KEY(role) REFERENCES roles(role_name)
            );""")

con.execute("""CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user INTEGER NOT NULL,
                date TEXT NOT NULL,
                time_utc INTEGER NOT NULL,
                type INTEGER NOT NULL,
                FOREIGN KEY(user) REFERENCES users(user_id)
            );""")

con.execute("""CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user INTEGER NOT NULL,
                date TEXT NOT NULL,
                active_time_utc INTEGER NOT NULL,
                difference_utc INTEGER NOT NULL
            );""")

logger.info("Подготовка базы данных к работе завершено")
con.close()


class ActivityType(Enum):
    START = 1
    STOP = 0


def get_user_by_vk_id(user_id: int) -> Optional[User]:
    with sqlite3.connect(PATH_TO_DATABASE) as con:
        # Получение пользователя
        query_user = con.execute("""SELECT * FROM users WHERE user_id={}""".format(user_id))
        raw_user = query_user.fetchone()
        
        if not raw_user:
            return None
        
        # Формирование схемы пользователя
        user = User(
            id=raw_user[0],
            user_id=raw_user[1],
            role=get_role_by_name(raw_user[2]),
            state=raw_user[3]
        )
        
        return user


def get_all_vk_ids():
    with sqlite3.connect(PATH_TO_DATABASE) as con:
        query_vk_ids = con.execute("""SELECT user_id FROM users""")
        vk_ids = query_vk_ids.fetchall()
        return vk_ids


def get_role_by_name(name: str) -> Optional[Role]:
    with sqlite3.connect(PATH_TO_DATABASE) as con:
        # Получение роли
        query_role = con.execute("""SELECT * FROM roles WHERE role_name='{}'""".format(name))
        raw_role = query_role.fetchone()
        
        if not raw_role:
            return None
        
        role = Role(
            id=raw_role[0],
            role_name=raw_role[1],
            daily_norm=raw_role[2]
        )
        
        return role


def get_activities_by_user(user: User, date: str) -> List[Activity]:
    with sqlite3.connect(PATH_TO_DATABASE) as con:
        query_activities = con.execute("""SELECT * FROM activities WHERE user={} AND date='{}'""".format(user.user_id, date))
        raw_activities = query_activities.fetchall()
        
        activities = list(
            map(
                lambda activity: Activity(
                    id=activity[0],
                    user=user,
                    date=activity[2],
                    time_utc=activity[3],
                    type=activity[4]
                ), raw_activities
            )
        )
        
        return activities


def get_results_by_date(date: str) -> List[Result]:
    with sqlite3.connect(PATH_TO_DATABASE) as con:
        query_results = con.execute("""SELECT * FROM results WHERE date='{}'""".format(date))
        raw_results = query_results.fetchall()
        results = list(map(lambda r: Result(
            id=r[0],
            user=get_user_by_vk_id(r[1]),
            date=r[2],
            active_time_utc=r[3],
            difference_utc=r[4]
        ), raw_results))
        return results


def update_user(user: User):
    with sqlite3.connect(PATH_TO_DATABASE) as con:
        con.execute("""UPDATE users
                    SET role = '{}',
                        state = {}
                    WHERE user_id={}""".format(user.role.role_name, 0 if user.state == ActivityType.STOP else 1, user.user_id))
        con.commit()


def add_activity(activity: Activity):
    with sqlite3.connect(PATH_TO_DATABASE) as con:
        con.execute("""INSERT INTO activities (user, date, time_utc, type)
                    VALUES ({}, '{}', {}, {})""".format(
                        activity.user.user_id, activity.date, activity.time_utc, activity.type
                        )
                    )
        con.commit()
        

def add_result(result: Result):
    with sqlite3.connect(PATH_TO_DATABASE) as con:
        con.execute("""INSERT INTO results (user, date, active_time_utc, difference_utc)
                    VALUES ({}, '{}', {}, {})""".format(result.user.user_id, result.date, result.active_time_utc, result.difference_utc))
        con.commit()

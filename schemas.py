from typing import Optional

from pydantic import BaseModel


class Base(BaseModel):
    id: Optional[int] = None


class Role(Base):
    role_name: str
    daily_norm: int
    

class User(Base):
    user_id: int
    role: Role
    state: int
    
    def to_url(self) -> str:
        return f"https://vk.com/id{self.user_id}"


class Activity(Base):
    user: User
    date: str
    time_utc: int
    type: int
    

class Result(Base):
    user: User
    date: str
    active_time_utc: int
    difference_utc: int
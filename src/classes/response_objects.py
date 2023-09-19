from typing import Union
from uuid import UUID
from pydantic import BaseModel
from enum import Enum

class TimerStatus(str, Enum):
    waiting = 'waiting'
    executing = 'executing'
    done = 'done'
    failed = 'failed'

class SetTimerResponse(BaseModel):
    id: UUID = ""
    time_left: int


class GetTimerResponse(BaseModel):
    id: UUID = ""
    status: TimerStatus = TimerStatus.waiting 
    time_left: int = 0
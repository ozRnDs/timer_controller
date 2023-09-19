from pydantic import BaseModel
from datetime import datetime


class TimerInformation(BaseModel):
    timer_id: str
    timer_url: str
    timer_status: str
    timer_date: datetime

    def for_sql_query(self):
        return {
            "timer_id": self.timer_id,
            "timer_url": self.timer_url,
            "timer_status": self.timer_status,
            "timer_date": self.get_date_sql_format(self.timer_date)
        }
    
    @staticmethod
    def get_date_sql_format(date_to_convert: datetime):
        return date_to_convert.strftime('%Y-%m-%d %H:%M:%S')
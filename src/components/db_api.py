from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel
from typing import List
from fastapi import HTTPException

import time 

import logging
logger = logging.getLogger(__name__)

import mysql.connector

from config.config import app_config
from classes.response_objects import TimerStatus

TABLES = {}
TABLES['timers'] = (
    "CREATE TABLE timers ("
    " timer_id BINARY(16) PRIMARY KEY,"
    " timer_url VARCHAR(2083),"
    " timer_status ENUM ('waiting','executing','done','failed') NOT NULL,"
    " timer_invoke_time DATETIME NOT NULL)"
    " ENGINE=InnoDB"
)

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

class DbApi():

    def __init__(self,
                 user,password,host,database) -> None:           
        try:
            self.db_connection = self.connect_to_db(user=user, password=password, host=host, database=database)
            logger.info(f"Connected to DB. HOST={host}, DATABASE={database}")
        except Exception as err:
            logger.error(f"Couldn't connect to DB: {err}")

    def insert_timer(self, timer_url, timer_invoke_date: datetime) -> str:
        
        insert_query = "INSERT INTO timers (timer_id,timer_url, timer_status,timer_invoke_time) VALUES (UUID_TO_BIN(%(timer_id)s),%(timer_url)s,%(timer_status)s,%(timer_date)s)"

        db_cursor = self.db_connection.cursor()

        insert_data = TimerInformation(timer_id=str(uuid4()),
                                       timer_url=str(timer_url),
                                       timer_status=TimerStatus.waiting.value,
                                       timer_date=timer_invoke_date)

        try:
            db_cursor.execute(insert_query,insert_data.for_sql_query())
            self.db_connection.commit()
        except mysql.connector.Error as err:
            if err.errno != 1146:
                logger.error(f"Unexpected DB Error: {err}")
                raise HTTPException(status_code=500, detail="Failed to communicate with db")
            self.create_table(TABLES["timers"])
            db_cursor.execute(insert_query,insert_data)
        except Exception as err:
            logger.error(f"Unexpected Error: {err}")
            raise HTTPException(status_code=500, detail="Could not save the job to the server")
        finally:
            if db_cursor:
                db_cursor.close()
        return insert_data.timer_id


    
    def get_timer_information(self, timer_uuid) -> TimerInformation:
        
        get_query = "SELECT BIN_TO_UUID(timer_id), timer_url, timer_status, timer_invoke_time from timers where timer_id=UUID_TO_BIN(%(timer_id)s)"

        db_cursor = self.db_connection.cursor()

        select_data = {
            "timer_id": timer_uuid
        }
        try:
            db_cursor.execute(get_query,select_data)
            response = db_cursor.fetchone()
        except mysql.connector.Error as err:
            if err.errno!=1411:
                logger.error(f"Unexpected Error: {err}")
                raise HTTPException(status_code=500, detail="Failed to communicate with db")
            raise HTTPException(status_code=400, detail="Illegal UUID")
        except Exception as err:
            logger.error(f"Unexpected Error: {err}")
            raise HTTPException(status_code=500, detail="Unexpected Error")
        finally:
            if db_cursor:
                db_cursor.close()
        if not response:
            return {}
        timer_id, timer_url, timer_status, timer_invoke_time = response
        return TimerInformation(timer_id=timer_id, timer_url=timer_url, timer_status=timer_status, timer_date=timer_invoke_time)

    def get_tasks_to_be_executed_at_time(self, execusion_time, limit=2)-> List[TimerInformation]:
        get_tasks_query = "Select BIN_TO_UUID(timer_id), timer_url, timer_status, timer_invoke_time from timers where timer_invoke_time <= %(execution_time)s and timer_status='waiting' LIMIT %(limit)s FOR UPDATE SKIP LOCKED" #ORDER BY timer_invoke_time DESC
        # update_tasks_query = "Update timers SET timer_status='executing' where BIN_TO_UUID(timer_id) in (%s)"

        sql_data = {
            "execution_time": execusion_time,
            "limit": limit
        }

        db_cursor = self.db_connection.cursor()
        tasks_to_execute = []
        try:
            db_cursor.execute("START TRANSACTION")
            db_cursor.execute(get_tasks_query,sql_data)
            responses = db_cursor.fetchall()
            for response in responses:
                timer_id, timer_url, timer_status, timer_invoke_time = response
                tasks_to_execute.append(TimerInformation(timer_id=timer_id,
                                                         timer_url=timer_url,
                                                         timer_status=timer_status,
                                                         timer_date=timer_invoke_time))
        except mysql.connector.Error as err:
            logger.error(f"Error featching data from db: {err}")
            raise HTTPException(status_code=500, detail="Comuunication Error with DB")
        except Exception as err:
            logger.error(f"Unexpected Error Occured: {err}")
            raise HTTPException(status_code=500, detail="Unexpected Error Occured")
        finally:
            # time.sleep(10)
            if db_cursor:
                self.current_cursor = db_cursor
        return tasks_to_execute
    
    def update_done_tasks(self, list_of_tasks):

        db_cursor = self.current_cursor
        update_query = "UPDATE timers SET timer_status='done' WHERE BIN_TO_UUID(timer_id) in (%s)"

        try:
            db_cursor.execute(update_query, list_of_tasks)
            self.db_connection.commit()
        except mysql.connector.Error as err:
            logger.error(f"Unexpected DB Error: {err}")
            raise HTTPException(status_code=500, detail="Failed to communicate with db")
        except Exception as err:
            logger.error(f"Unexpected Error: {err}")
            raise HTTPException(status_code=500, detail="Could not update the job as done")
        finally:
            if db_cursor:
                db_cursor.close()

    def connect_to_db(self, user,password,host,database):
        try:
            return mysql.connector.connect(user=user,
                                    password=password,
                                    host=host,
                                    database=database)
        except mysql.connector.Error as err:
            if err.errno == 1049: # No database
                self.create_db(mysql.connector.connect(user=user,password=password,host=host), database=database)
                return self.connect_to_db(user=user, password=password, host=host, database=database)
        except Exception as err:
            logger.error(f"Unexpected Error: {err}")

    def create_table(self, table_query):
        try:
            db_cursor = self.db_connection.cursor()
            db_cursor.execute(table_query)

            db_cursor.close()
        except Exception as err:
            logger.error(f"Failed to create table: {err}")

    def create_db(self, connection, database):
        try:
            db_cursor = connection.cursor()
            query_data = {
                "database": database
            }

            db_cursor.execute(f"CREATE DATABASE {database}")

            # db_cursor.commit()
            db_cursor.close()
            connection.close()
        except Exception as err:
            logger.error(f"Unexpected error while create db: {err}")
            breakpoint()


    def __del__(self):
        try:
            if (self.current_cursor):
                    self.current_cursor.close()
            if (self.db_connection):
                self.db_connection.close()
            logger.info("Connection to db is closed")
        except Exception as err:
            logger.error(f"Couldn't close DB Connection: {err}")

db_instance = DbApi(user=app_config.db_user,
                    password=app_config.db_password,
                    host=app_config.db_host,
                    database=app_config.db_name)
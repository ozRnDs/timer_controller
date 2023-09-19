from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel
from typing import List

import time 

import logging
logger = logging.getLogger(__name__)

import mysql.connector

from config.config import app_config
from classes.response_objects import TimerStatus
from classes.timer import TimerInformation

TABLES = {}
TABLES['timers'] = (
    "CREATE TABLE timers ("
    " timer_id BINARY(16) PRIMARY KEY,"
    " timer_url VARCHAR(2083),"
    " timer_status ENUM ('waiting','executing','done','failed') NOT NULL,"
    " timer_invoke_time DATETIME NOT NULL)"
    " ENGINE=InnoDB"
)

class DbApi():
    db_connection = None
    reconnect_tries = 0
    def __init__(self,
                 user,password,host,database) -> None:           
        try:
            self.user = user
            self.password = password
            self.host=host
            self.database=database
            self.db_connection = self.connect_to_db()

        except Exception as err:
            logger.error(f"Couldn't connect to DB: {err}")

    def insert_timer(self, timer_url, timer_invoke_date: datetime) -> str:
        
        insert_query = "INSERT INTO timers (timer_id,timer_url, timer_status,timer_invoke_time) VALUES (UUID_TO_BIN(%(timer_id)s),%(timer_url)s,%(timer_status)s,%(timer_date)s)"

        

        insert_data = TimerInformation(timer_id=str(uuid4()),
                                       timer_url=str(timer_url),
                                       timer_status=TimerStatus.waiting.value,
                                       timer_date=timer_invoke_date)

        try:
            db_cursor = self.db_connection.cursor()
            db_cursor.execute(insert_query,insert_data.for_sql_query())
            self.db_connection.commit()
        except mysql.connector.Error as err:
            if err.errno != 1146:
                self.__error_handler__(err)
            self.create_table(TABLES["timers"])
            db_cursor.execute(insert_query,insert_data)
        except Exception as err:
            self.__error_handler__(err)
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

    def get_tasks_to_be_executed_at_time(self, execusion_time, limit: int=2)-> List[TimerInformation]:
        get_tasks_query = "Select BIN_TO_UUID(timer_id), timer_url, timer_status, timer_invoke_time from timers where timer_invoke_time <= %(execution_time)s and timer_status='waiting' LIMIT %(limit)s FOR UPDATE SKIP LOCKED" #ORDER BY timer_invoke_time DESC
        # update_tasks_query = "Update timers SET timer_status='executing' where BIN_TO_UUID(timer_id) in (%s)"

        sql_data = {
            "execution_time": execusion_time,
            "limit": limit
        }

        
        tasks_to_execute = []
        db_cursor = None
        try:
            db_cursor = self.db_connection.cursor()
            db_cursor.execute("START TRANSACTION")
            db_cursor.execute(get_tasks_query,sql_data)
            responses = db_cursor.fetchall()
            for response in responses:
                timer_id, timer_url, timer_status, timer_invoke_time = response
                tasks_to_execute.append(TimerInformation(timer_id=timer_id,
                                                         timer_url=timer_url,
                                                         timer_status=timer_status,
                                                         timer_date=timer_invoke_time))
        except Exception as err:
            self.__error_handler__(err)
        finally:
            # time.sleep(10)
            if db_cursor:
                self.current_cursor = db_cursor
        return tasks_to_execute
    
    def update_tasks_status(self, list_of_tasks: List[str], status: str):
        if len(list_of_tasks)==0:
            return
        db_cursor = self.current_cursor
        format_strings = ','.join(['%s'] * len(list_of_tasks))
        update_query = "UPDATE timers SET timer_status=%%s WHERE BIN_TO_UUID(timer_id) in (%s)" % format_strings
        try:
            db_cursor.execute(update_query, [status]+list_of_tasks)
            self.db_connection.commit()
        except Exception as err:
            self.__error_handler__(err)
        finally:
            if db_cursor:
                db_cursor.close()

    def connect_to_db(self):
        if self.reconnect_tries > 10:
            self.reconnect_tries=0
            raise ConnectionError("Can't establish connection to DB (10 reties)")
        try:
            self.reconnect_tries+=1
            connection = mysql.connector.connect(user=self.user,
                                    password=self.password,
                                    host=self.host,
                                    database=self.database)
            self.reconnect_tries = 0
            logger.info(f"Connected to DB. HOST={self.host}, DATABASE={self.database}")
            return connection
        except mysql.connector.Error as err:
            if err.errno == 1049: # No database
                self.create_db(mysql.connector.connect(user=self.user,password=self.password,host=self.host), database=self.database)
                return self.connect_to_db(user=self.user, password=self.password, host=self.host, database=self.database)
            self.__error_handler__(err)
        except Exception as err:
            self.__error_handler__(err)

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

    def __error_handler__(self,err):
        if not self.db_connection:
            self.__db_reconnect_handler__()
        if type(err) in (mysql.connector.errors.OperationalError, mysql.connector.errors.DatabaseError, mysql.connector.Error):
            if 'MySQL Connection not available' in str(err) or err.errno in (2013,2003):
                self.__db_reconnect_handler__()
            raise Exception(f"DB Error: {err}")
        # logger.error(f"Unexpected Error: {err}")
        raise Exception(f"Unexpected Error: {err}")

    def __db_reconnect_handler__(self):
        logger.error(f"Lost Connection to DB. Sleep for 1 seconds and reconnect again")
        time.sleep(1)
        self.db_connection=self.connect_to_db()
        if not self.db_connection:
            raise ConnectionError("Could not Reconnect to DB ") 
        return
    
db_instance = DbApi(user=app_config.DB_USER,
                    password=app_config.DB_PASSWORD,
                    host=app_config.DB_HOST,
                    database=app_config.DB_NAME)

# TODO: Main exception handler for the class
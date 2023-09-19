import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
import pytest
import sys, os

# SET UP SRC LIBRARY FOR TESTINGS
current_library = os.getcwd()
sys.path.append(current_library+"/src")
logger.info(f"Current Library: {current_library}")
logger.info(f"Project Paths: {sys.path}")


from unittest.mock import patch
from components.db_api import DbApi

@pytest.fixture(scope="function")
def db_fixture()-> DbApi:
    db_instance = DbApi(user="root", password="1234", host="127.0.0.1", database="timer_db")
    clean_timer_table_query = "Delete from timers"
    
    db_cursor = db_instance.db_connection.cursor()
    db_cursor.execute(clean_timer_table_query)
    db_instance.db_connection.commit()
    if db_cursor:
        db_cursor.close()
        
    yield db_instance

    db_instance = ""    

@pytest.fixture(scope="function")
def secondary_db_fixture()-> DbApi:
    db_instance = DbApi(user="root", password="1234", host="127.0.0.1", database="timer_db")

    yield db_instance

    db_instance = ""    
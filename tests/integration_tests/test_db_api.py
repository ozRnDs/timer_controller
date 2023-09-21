import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import pytest
from typing import List
from datetime import datetime

from components.db_api import DbApi, TimerInformation

@pytest.fixture()
def test_date_fixture():
    test_datetime = datetime(month=9, year=1091, day=19, hour=9, minute=30)
    return test_datetime

def test_get_tasks_to_be_executed_at_time(db_fixture: DbApi):
    
    db_fixture.insert_timer("test_timer1", 
                            datetime(month=9, year=2022, day=19, hour=9, minute=30))
    db_fixture.insert_timer("test_timer1", 
                            datetime(month=9, year=2022, day=19, hour=9, minute=30))

    list_of_tasks = db_fixture.get_tasks_to_be_executed_at_time(datetime(month=9, year=2023, day=19, hour=9, minute=30))

    assert len(list_of_tasks) == 2

def test_multiple_task_request(db_fixture: DbApi, secondary_db_fixture: DbApi, test_date_fixture):
    # SETUP
    
    
    db_fixture.insert_timer("test_timer1", 
                            datetime(month=9, year=1090, day=19, hour=9, minute=30))
    db_fixture.insert_timer("test_timer1", 
                            datetime(month=9, year=1090, day=19, hour=9, minute=30))
    db_fixture.insert_timer("test_timer1", 
                            datetime(month=9, year=1090, day=19, hour=9, minute=30))
    db_fixture.insert_timer("test_timer1", 
                            datetime(month=9, year=1090, day=19, hour=9, minute=30))
    
    total_number_of_tasks_expected = db_fixture.get_tasks_to_be_executed_at_time(test_date_fixture,limit=100)
    list_of_tasks_origin = [task.timer_id for task in total_number_of_tasks_expected]
    db_fixture.update_tasks_status(list_of_tasks_origin,'waiting')
    
    # ASSERT
    list_of_tasks1 = db_fixture.get_tasks_to_be_executed_at_time(test_date_fixture,limit=3)
    list_of_tasks2 = secondary_db_fixture.get_tasks_to_be_executed_at_time(test_date_fixture,limit=100)

    assert 0 < len(list_of_tasks1) == 3
    assert 0 < len(list_of_tasks2) == len(total_number_of_tasks_expected)-len(list_of_tasks1)
    logger.info(f"Total Tasks: {len(total_number_of_tasks_expected)}\t|\tList 1: {len(list_of_tasks1)}\t|\tList 2:{len(list_of_tasks2)}")

    

def test_update_task_as_done(db_fixture: DbApi, test_date_fixture):
    # SETUP
    example_task_id = db_fixture.insert_timer("test_update_task", 
                      datetime(month=9, year=1090, day=19, hour=9, minute=30))
    example_task_id = db_fixture.insert_timer("test_update_task", 
                      datetime(month=9, year=1090, day=19, hour=9, minute=30))


    task_information = db_fixture.get_timer_information(example_task_id)
    assert task_information.timer_status == 'waiting'

    list_of_tasks1: List[TimerInformation] = db_fixture.get_tasks_to_be_executed_at_time(test_date_fixture)
    list_of_tasks_id = [task_info.timer_id for task_info  in list_of_tasks1]
    # ASSERT
    db_fixture.update_tasks_status(list_of_tasks_id,'done')

    # ASSERT
    task_information = db_fixture.get_timer_information(example_task_id)
    assert task_information.timer_status == 'done'

    



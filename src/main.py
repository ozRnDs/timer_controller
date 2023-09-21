from datetime import datetime
import time
import asyncio
# import aiohttp

from typing import List
from components.db_api import db_instance, TimerInformation
from components.task_executer import tasks_launcher
from config.config import app_config



async def controller_main_loop():
    app_config.logger.info("Controller is listening to db")
    error_counter = 0
    wait_flag = True
    while True:
        try:

            list_of_tasks = await main_controller_logic()
            error_counter=0

            if len(list_of_tasks)==app_config.BATCH_SIZE:
                wait_flag=False
        except Exception as err:
            app_config.logger.error(f"Unexpected Error: {err}")
            error_counter += 1
            if error_counter > app_config.RETRY_NUMBER:
                app_config.logger.critical("Service Can't recover from error. Shutting Down")
                exit(0)
        if wait_flag:
            await asyncio.sleep(0.5*(1+error_counter))
        await asyncio.sleep(0.05)
        wait_flag=True

async def main_controller_logic():
    list_of_tasks: List[TimerInformation] = db_instance.get_tasks_to_be_executed_at_time(datetime.now(), limit=app_config.BATCH_SIZE)
    
    start_time = time.perf_counter()

    list_of_tasks_ids = [item_id.timer_id for item_id in list_of_tasks]
    db_instance.update_tasks_status(list_of_tasks_ids,'executing')
    handled_tasks = await tasks_launcher(list_of_tasks)

    tasks_failed = [item_id.timer_id for item_id in list_of_tasks if not item_id.timer_id in handled_tasks]
    db_instance.update_tasks_status(handled_tasks,'done')
    db_instance.update_tasks_status(tasks_failed,'failed')

    run_time= time.perf_counter() - start_time

    app_config.logger.info(f"Handled {len(list_of_tasks)} tasks in {run_time} seconds")
    return list_of_tasks

if __name__ == "__main__":
    asyncio.run(controller_main_loop())

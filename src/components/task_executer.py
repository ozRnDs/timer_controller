import logging
logger = logging.getLogger(__name__)

import asyncio
import aiohttp
from typing import List

from classes.timer import TimerInformation


async def tasks_launcher(list_of_tasks: List[TimerInformation]):   
    async with aiohttp.ClientSession() as session:
        
        url_requests = []
        for task in list_of_tasks:
            url_to_invoke = task.timer_url + "/" + task.timer_id
            url_requests.append(get_url(session,url_to_invoke,task.timer_id))

        all_responses = await asyncio.gather(*url_requests)
        return [response_item for response_item in all_responses if response_item]
        

async def get_url(session, url,task_id):
    try:
        async with session.post(url) as response:
            if response.status == 200:
                return task_id
            return
    except Exception as err:
        pass
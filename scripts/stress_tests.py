import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
from datetime import datetime
import time

import sys, os

# SET UP SRC LIBRARY FOR TESTINGS
current_library = os.getcwd()
sys.path.append(current_library+"/src")
logger.info(f"Current Library: {current_library}")
logger.info(f"Project Paths: {sys.path}")

from components.db_api import db_instance


if __name__ == "__main__":
    # Create a loop that sends many tasks to be invoked inorder to check the service ability to handle them.
    for i in range(10000):
        db_instance.insert_timer(f"http://127.0.0.1/", datetime.now())
        time.sleep(0.01)
import os
import logging
logging.basicConfig(format='%(asctime)s.%(msecs)05d | %(levelname)s | %(filename)s:%(lineno)d | %(message)s' , datefmt='%FY%T')

class ApplicationConfiguration:

    db_host: str = "127.0.0.1"
    db_name: str = "timer_db"
    db_user: str = "root"
    db_password: str = "1234"


    def __init__(self) -> None:
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.logger.info("Start App")

        self.extract_env_variables()
        

    def extract_env_variables(self):
        for attr in self.__annotations__:
            try:
                self.__setattr__(attr, os.environ[attr])
            except Exception as err:
                self.logger.warning(f"Couldn't find {attr} in environment. Run with default")
                pass
        
app_config = ApplicationConfiguration()
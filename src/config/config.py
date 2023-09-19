import os
import logging
logging.basicConfig(format='%(asctime)s.%(msecs)05d | %(levelname)s | %(filename)s:%(lineno)d | %(message)s' , datefmt='%FY%T')

class ApplicationConfiguration:

    DB_HOST: str = "127.0.0.1"
    DB_NAME: str = "timer_db"
    DB_USER: str = "root"
    DB_PASSWORD: str = "1234" # Should be extracted from sercret in production case

    
    BATCH_SIZE: int = 10

    RETRY_NUMBER: int = 10

    RECONNECT_WAIT_TIME: int = 1



    def __init__(self) -> None:
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        self.extract_env_variables()
        self.logger.info(f"Loading Worker with batch size: {self.BATCH_SIZE}")

    def extract_env_variables(self):
        for attr, attr_type in self.__annotations__.items():
            try:
                self.__setattr__(attr, (attr_type)(os.environ[attr]))
            except Exception as err:
                self.logger.warning(f"Couldn't set {attr} from environment variable. Running with default value")
                pass
        
app_config = ApplicationConfiguration()
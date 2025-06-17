import logging
import os
from dotenv import load_dotenv  
from datetime import datetime
from posthog import Posthog

load_dotenv()

posthog = Posthog(os.getenv('POSTHOG_API_KEY'), host=os.getenv('POSTHOG_HOST'))

class PosthogHandler(logging.Handler):
    def emit(self, record):
        posthog.capture(
            'logging',
            event='log',
            properties={'message': record.getMessage(), 'level': record.levelname, 'filename': record.filename, 'lineno': record.lineno, 'datetime': datetime.now()}
        )

posthog_handler = PosthogHandler()

def get_logger(name: str):
    # Configure the logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create a console handler and set its level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create a formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(posthog_handler)
    return logger

from os import path, environ
from dotenv import load_dotenv

class Environment():
    def __init__(self):
        try:
            dotenv_path = path.join(path.dirname(__file__), '.env')
            load_dotenv(dotenv_path)
        except Exception as e:
            raise

        self.DB_URI = environ.get('DB_URI')
        self.TOKEN = environ.get('TOKEN')



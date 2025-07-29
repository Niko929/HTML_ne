from dotenv import load_dotenv
import os

load_dotenv()


def config():
    return {
        'host': os.getenv('HOST'),
        'port': os.getenv('PORT'),
        'user': os.getenv('USER'),
        'password': os.getenv('PASSWORD'),
        'database': os.getenv('NAME')
    }

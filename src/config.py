from dotenv import load_dotenv
import os

load_dotenv(override=True)


def config():
    return {
        "host": os.getenv("HOST"),
        "port": os.getenv("PORT"),
        "user": os.getenv("USER"),
        "password": os.getenv("PASSWORD"),
    }
employer_ids = [
        1740,  # Яндекс
        15478,  # VK
        3529,  # Сбер
        78638,  # Тинькофф
        1122462,  # СБИС
        2180,  # Ozon
        87021,  # Wildberries
        3776,  # МТС
        41862,  # Авито
        4934,  # Билайн
    ]
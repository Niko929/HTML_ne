import abc
from pprint import pprint

import requests


class JobAPI(abc.ABC):
    @abc.abstractmethod
    def _connect(self):
        """Метод для подключения API"""
        pass

    @abc.abstractmethod
    def get_vacancion(self, keyword: str, page: int):
        """Метод для получения вакансий по ключевому слову"""
        pass


class hh_API(JobAPI):
    __BASE_URL = "https://api.hh.ru/vacancies"

    def __init__(self):
        self.__session = None

    def _connect(self):
        """Метод для подключения API"""
        self.__session = requests.Session()
        response = self.__session.get(self.__BASE_URL)
        response.raise_for_status()
        return response

    def get_vacancion(self, keyword: str, page: int, per_page: int = 100):
        """Метод для получения по ключевому слову"""
        self._connect()
        params = {"text": keyword, "per_page": per_page, "page": page}

        response = self.__session.get(self.__BASE_URL, params=params)
        response.raise_for_status()
        vacancies = response.json().get("items", [])

        return [
            {
                "name": vacan["name"],
                "company": vacan["employer"]["name"],
                "url": vacan["alternate_url"],
                "salary": vacan["salary"],
                "id": vacan["id"],
            }
            for vacan in vacancies
        ]

if __name__ == "__main__":
    hh_api = hh_API()
    vacancies = hh_api.get_vacancion("Python", 2)
    try:
        for vacan in vacancies:
            salary = vacan["salary"]
            if salary and salary["from"] is not None and salary["to"] is not None:
                aver_salary = salary["from"] + (salary["to"] - salary["from"]) / 2
            elif salary and salary["from"] is not None:
                aver_salary = salary["from"]
            elif salary and salary["to"] is not None:
                aver_salary = salary["to"]
            else:
                aver_salary = 0

            pprint(
                f"Название вакансии: {vacan['name']},"
                f"Работодатель: {vacan['company']}, "
                f"Ссылка:{vacan['url']} "
                f"Средняя зарпалата: {vacan['salary']}"
                f"id: {vacan['id']}"
            )
    except Exception as e:
        print(f"Произошла ошибка: {e}")
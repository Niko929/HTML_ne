import requests


def get_employers(employer_ids: str) -> list:
    """Получить список работодателей по ключевому запросу."""
    url = f"https://api.hh.ru/employers/{employer_ids}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_vacancies_by_employer(employer_ids: int, per_page: int = 10) -> list:
    """Получить вакансии конкретного работодателя."""
    url = f"https://api.hh.ru/vacancies/"
    params = {
        "employer_id": employer_ids,
        "per_page": per_page,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["items"]

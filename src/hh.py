import requests


def get_employers(query: str, per_page: int = 10) -> list:
    """Получить список работодателей по ключевому запросу."""
    url = "https://api.hh.ru/employers"
    params = {
        "text": query,
        "per_page": per_page,
        "only_with_vacancies": True,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["items"]


def get_vacancies_by_employer(employer_id: int, per_page: int = 10) -> list:
    """Получить вакансии конкретного работодателя."""
    url = f"https://api.hh.ru/vacancies"
    params = {
        "employer_id": employer_id,
        "per_page": per_page,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["items"]






# company_names = [
#     "Яндекс", "Тинькофф", "Сбербанк", "VK", "Лаборатория Касперского",
#     "1С", "Ростелеком", "Ozon", "Wildberries", "Авито"
# ]
#
# employers_data = []
# for company in company_names:
#     employers = get_employers(company, per_page=1)
#     if employers:
#         employers_data.append(employers[0])
#     time.sleep(1)  # Чтобы не превысить лимиты API



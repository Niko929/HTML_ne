import requests



def get_employers_data(employer_ids):
    """Получение данных о работодателях с обработкой отсутствующих полей"""
    employers = []
    base_url = "https://api.hh.ru/employers/"

    for employer_id in employer_ids:
        try:
            response = requests.get(f"{base_url}{employer_id}")
            response.raise_for_status()  # Проверка на ошибки HTTP
            data = response.json()

            # Проверяем наличие обязательных полей
            if 'id' not in data or 'name' not in data:
                print(f"У работодателя {employer_id} отсутствуют обязательные поля")
                continue

            employer = {
                'id': data['id'],
                'name': data['name'],
                'description': data.get('description', ''),
                'site_url': data.get('site_url', ''),
                'vacancies_url': data.get('vacancies_url', '')
            }
            employers.append(employer)

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе работодателя {employer_id}: {e}")

    return employers


def get_vacancies_data(employer_ids):
    """Получение данных о вакансиях с обработкой отсутствующих полей"""
    vacancies = []
    base_url = "https://api.hh.ru/vacancies"

    for employer_id in employer_ids:
        try:
            params = {
                'employer_id': employer_id,
                'per_page': 100,  # Максимальное количество вакансий
                'only_with_salary': True  # Только вакансии с указанной зарплатой
            }

            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'items' not in data:
                print(f"Нет данных о вакансиях для работодателя {employer_id}")
                continue

            for item in data['items']:
                try:
                    # Обработка зарплаты
                    salary = None
                    if item.get('salary'):
                        salary_data = item['salary']
                        salary_from = salary_data.get('from')
                        salary_to = salary_data.get('to')

                        # Берем верхнюю границу зарплаты, если указана
                        salary = salary_to if salary_to else salary_from

                    # Проверяем обязательные поля
                    if 'id' not in item or 'name' not in item or 'alternate_url' not in item:
                        print(f"У вакансии работодателя {employer_id} отсутствуют обязательные поля")
                        continue

                    vacancy = {
                        'id': item['id'],
                        'employer_id': employer_id,
                        'name': item['name'],
                        'salary': salary,
                        'url': item['alternate_url'],
                        'description': item.get('description', '')
                    }
                    vacancies.append(vacancy)

                except KeyError as e:
                    print(f"Ошибка в структуре вакансии: {e}")
                    continue

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе вакансий работодателя {employer_id}: {e}")

    return vacancies


# Пример списка ID интересных компаний (проверенные работодатели)
employer_ids = [
    '15478',  # VK
    '78638',  # Тинькофф
    '3529',  # Сбер
    '1740',  # Яндекс
    '3776',  # МТС
    '41862',  # Ozon
    '87021',  # Wildberries
    '2180',  # Лаборатория Касперского
    '1122462',  # СберТех
    '4934'  # Билайн
]

# Получаем данные с обработкой ошибок
try:
    employers = get_employers_data(employer_ids)
    print(f"Получено {len(employers)} работодателей")

    vacancies = get_vacancies_data(employer_ids)
    print(f"Получено {len(vacancies)} вакансий")

except Exception as e:
    print(f"Ошибка при получении данных: {e}")
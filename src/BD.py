import requests
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch
import time
from typing import Dict, List, Optional, Tuple


class HHAPI:
    """Класс для работы с API HeadHunter"""

    @staticmethod
    def get_employers(employer_ids: List[str]) -> List[Dict]:
        """Получение информации о работодателях по их ID"""
        employers = []
        url = "https://api.hh.ru/employers/"
        headers = {"User-Agent": "HH-User-Agent"}

        for employer_id in employer_ids:
            try:
                response = requests.get(url.format(employer_id=employer_id), headers=headers)
                response.raise_for_status()
                employer_data = response.json()

                employers.append({
                    'name': employer_data.get('name'),
                    'url': employer_data.get('alternate_url'),
                    'description': employer_data.get('description'),
                    'open_vacancies': employer_data.get('open_vacancies', 0),
                    'hh_id': employer_data.get('id'),
                    'trusted': employer_data.get('trusted', False)
                })

                # Задержка для соблюдения лимитов API
                time.sleep(0.5)

            except requests.exceptions.RequestException as e:
                print(f"Ошибка при получении данных работодателя {employer_id}: {e}")

        return employers

    @staticmethod
    def get_employer_vacancies(employer_id: str) -> List[Dict]:
        """Получение вакансий работодателя"""
        vacancies = []
        url = "https://api.hh.ru/vacancies"
        headers = {"User-Agent": "HH-User-Agent"}
        params = {
            'employer_id': employer_id,
            'per_page': 100,  # Максимальное количество вакансий на странице
            'page': 0
        }

        try:
            while True:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                for item in data.get('items', []):
                    salary = item.get('salary')

                    vacancies.append({
                        'title': item.get('name'),
                        'description': item.get('description'),
                        'experience': item.get('experience', {}).get('name'),
                        'employment_mode': item.get('employment', {}).get('name'),
                        'address': item.get('area', {}).get('name'),
                        'hh_id': item.get('id'),
                        'url': item.get('alternate_url'),
                        'published_at': item.get('published_at'),
                        'salary': {
                            'currency': salary.get('currency') if salary else None,
                            'gross': salary.get('gross') if salary else None,
                            'from': salary.get('from') if salary else None,
                            'to': salary.get('to') if salary else None
                        } if salary else None
                    })

                # Проверяем, есть ли еще страницы
                params['page'] += 1
                if params['page'] >= data.get('pages', 1):
                    break

                # Задержка для соблюдения лимитов API
                time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении вакансий работодателя {employer_id}: {e}")

        return vacancies


import psycopg2
from psycopg2 import sql
from typing import List, Dict, Optional, Tuple


class DBManager:
    def __init__(self, dbname: str, user: str, password: str, host: str = 'localhost', port: str = '5432'):
        """Инициализация подключения к базе данных PostgreSQL"""
        self.conn = psycopg2.connect(
            dbname ='test',
            user = 'postgres',
            password = '1234',
            host = 'localhost',
            port = '5432'
        )
        self.conn.autocommit = True

    def __del__(self):
        """Закрытие соединения с базой данных при удалении объекта"""
        self.conn.close()

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """
        Получает список всех компаний и количество вакансий у каждой компании

        Returns:
            List[Tuple[str, int]]: Список кортежей (название компании, количество вакансий)
        """
        query = """
            SELECT e.employer_name, COUNT(v.vacancy_id) as vacancies_count
            FROM employers e
            LEFT JOIN vacancies v ON e.employer_id = v.employer_id
            GROUP BY e.employer_name
            ORDER BY vacancies_count DESC
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

    def get_all_vacancies(self) -> List[Dict[str, str]]:
        """
        Получает список всех вакансий с указанием названия компании,
        названия вакансии, зарплаты и ссылки на вакансию

        Returns:
            List[Dict[str, str]]: Список словарей с информацией о вакансиях
        """
        query = """
            SELECT 
                e.employer_name, 
                v.title, 
                COALESCE(s.from_amount, 0) as salary_from,
                COALESCE(s.to_amount, 0) as salary_to,
                COALESCE(s.currency, 'Не указана') as currency,
                v.url
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id
            LEFT JOIN salaries s ON v.vacancy_id = s.vacancy_id
            ORDER BY e.employer_name, v.title
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def get_avg_salary(self) -> float:
        """
        Получает среднюю зарплату по вакансиям

        Returns:
            float: Средняя зарплата
        """
        query = """
            SELECT AVG((COALESCE(from_amount, 0) + COALESCE(to_amount, 0)) / 2) as avg_salary
            FROM salaries
            WHERE from_amount > 0 OR to_amount > 0
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()
            return round(float(result[0]), 2) if result[0] else 0.0

    def get_vacancies_with_higher_salary(self) -> List[Dict[str, str]]:
        """
        Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям

        Returns:
            List[Dict[str, str]]: Список словарей с информацией о вакансиях
        """
        query = """
            SELECT 
                e.employer_name, 
                v.title, 
                COALESCE(s.from_amount, 0) as salary_from,
                COALESCE(s.to_amount, 0) as salary_to,
                COALESCE(s.currency, 'Не указана') as currency,
                v.url
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id
            JOIN salaries s ON v.vacancy_id = s.vacancy_id
            WHERE (COALESCE(s.from_amount, 0) + COALESCE(s.to_amount, 0)) / 2 > (
                SELECT AVG((COALESCE(from_amount, 0) + COALESCE(to_amount, 0)) / 2
                FROM salaries
                WHERE from_amount > 0 OR to_amount > 0
            )
            ORDER BY (COALESCE(s.from_amount, 0) + COALESCE(s.to_amount, 0)) / 2 DESC
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def get_vacancies_with_keyword(self, keyword: str) -> List[Dict[str, str]]:
        """
        Получает список всех вакансий, в названии которых содержатся переданные слова

        Args:
            keyword (str): Ключевое слово для поиска в названиях вакансий

        Returns:
            List[Dict[str, str]]: Список словарей с информацией о вакансиях
        """
        query = sql.SQL("""
            SELECT 
                e.employer_name, 
                v.title, 
                COALESCE(s.from_amount, 0) as salary_from,
                COALESCE(s.to_amount, 0) as salary_to,
                COALESCE(s.currency, 'Не указана') as currency,
                v.url
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id
            LEFT JOIN salaries s ON v.vacancy_id = s.vacancy_id
            WHERE v.title ILIKE %s OR v.description ILIKE %s
            ORDER BY e.employer_name, v.title
        """)
        with self.conn.cursor() as cur:
            search_pattern = f"%{keyword}%"
            cur.execute(query, (search_pattern, search_pattern))
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


if __name__ == "__main__":
    db_params = {
        'dbname': 'test',
        'user': 'postgres',
        'password': '1234',
        'host': 'localhost',
        'port': '5432'
    }
    db_manager = DBManager(**db_params)

    # Получение списка компаний и количества вакансий
    companies = db_manager.get_companies_and_vacancies_count()
    print("Компании и количество вакансий:")
    for company, count in companies:
        print(f"{company}: {count} вакансий")

    # Получение всех вакансий
    vacancies = db_manager.get_all_vacancies()
    print("\nВсе вакансии:")
    for vacancy in vacancies[:5]:  # Выводим первые 5 для примера
        print(f"{vacancy['employer_name']} - {vacancy['title']}")

    # Получение средней зарплаты
    avg_salary = db_manager.get_avg_salary()
    print(f"\nСредняя зарплата: {avg_salary}")

    # Получение вакансий с зарплатой выше средней
    high_salary_vacancies = db_manager.get_vacancies_with_higher_salary()
    print("\nВакансии с зарплатой выше средней:")
    for vacancy in high_salary_vacancies[:5]:  # Выводим первые 5 для примера
        print(f"{vacancy['employer_name']} - {vacancy['title']}")

    # Поиск вакансий по ключевому слову
    python_vacancies = db_manager.get_vacancies_with_keyword('python')
    print("\nВакансии с ключевым словом 'python':")
    for vacancy in python_vacancies[:5]:  # Выводим первые 5 для примера
        print(f"{vacancy['employer_name']} - {vacancy['title']}")
    # # ID работодателей на HeadHunter (примеры)
    # employer_ids = [
    #     '1740',  # Яндекс
    #     '15478',  # VK
    #     '3529',  # Сбер
    #     '78638',  # Тинькофф
    #     '1122462',  # СберТех
    #     '41862',  # 2ГИС
    #     '3776',  # МТС
    #     '39305',  # Газпром нефть
    #     '907345',  # Ростелеком
    #     '87021'  # Wildberries
    # ]

    # Параметры подключения к БД



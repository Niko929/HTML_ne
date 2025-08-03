import psycopg2
from src.config import config


class DBManager:
    """Класс для управления данными в БД PostgreSQL"""

    def __init__(self, db_name, params):

        self.db_name = db_name
        self.params = params.copy()
        self.params["database"] = self.db_name

    def get_companies_and_vacancies_count(self):
        """Получает список компаний и количество вакансий"""
        conn = None
        try:
            conn = psycopg2.connect(**self.params)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                       SELECT e.name, COUNT(v.id) as vacancies_count
                       FROM employers e
                       LEFT JOIN vacancies v ON e.id = v.employer_id
                       GROUP BY e.name
                       ORDER BY vacancies_count DESC
                   """
                )
                return cursor.fetchall()
        except Exception as e:
            print(f"Ошибка: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_all_vacancies(self):
        """Получает список всех вакансий с указанием компании, названия, зарплаты и ссылки"""
        conn = None
        try:
            conn = psycopg2.connect(**self.params)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        e.name as company_name,
                        v.title as vacancy_name,
                        CASE 
                            WHEN v.salary_from IS NOT NULL AND v.salary_to IS NOT NULL 
                                THEN v.salary_from || '-' || v.salary_to 
                            WHEN v.salary_from IS NOT NULL 
                                THEN 'от ' || v.salary_from 
                            WHEN v.salary_to IS NOT NULL 
                                THEN 'до ' || v.salary_to
                            ELSE 'не указана'
                        END as salary,
                        v.url
                    FROM vacancies v
                    JOIN employers e ON v.employer_id = e.id
                    ORDER BY company_name, vacancy_name
                """
                )
                return cur.fetchall()
        except Exception as e:
            print(f"Ошибка: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_avg_salary(self):
        """Получает среднюю зарплату по вакансиям (с учетом вилки зарплат)"""
        conn = psycopg2.connect(**self.params)

        with conn.cursor() as cur:
            # Вариант 1: Простое среднее между salary_from и salary_to
            cur.execute(
                """
                SELECT 
                   ROUND(AVG((COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) / 2), 2) as avg_salary
                FROM vacancies
                WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
            """
            )

            avg_salaries = cur.fetchone()
        conn.close()
        return avg_salaries

    def get_vacancies_with_higher_salary(self):
        """Получает список вакансий с зарплатой выше средней"""
        conn = psycopg2.connect(**self.params)
        avd = self.get_avg_salary()[0]
        with conn.cursor() as cur:
            # Затем получаем вакансии с зарплатой выше средней
            cur.execute(
                """
                SELECT 
                    e.name as company_name,
                    v.title as vacancy_name,
                    CASE 
                        WHEN v.salary_from IS NOT NULL AND v.salary_to IS NOT NULL 
                            THEN v.salary_from || '-' || v.salary_to 
                        WHEN v.salary_from IS NOT NULL 
                            THEN 'от ' || v.salary_from 
                        WHEN v.salary_to IS NOT NULL 
                            THEN 'до ' || v.salary_to 
                        ELSE 'не указана'
                    END as salary,
                    v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.id
                WHERE 
                    (v.salary_from IS NOT NULL AND v.salary_from > %s) OR
                    (v.salary_to IS NOT NULL AND v.salary_to > %s)
                ORDER BY 
                    CASE 
                        WHEN v.salary_from IS NOT NULL THEN v.salary_from
                        ELSE v.salary_to
                    END DESC
            """,
                (avd, avd),
            )
            vacancies = cur.fetchall()
        conn.close()
        return vacancies

    def get_vacancies_with_keyword(self, keyword):
        """Получает список вакансий, содержащих ключевое слово в названии"""
        conn = psycopg2.connect(**self.params)

        with conn.cursor() as cur:
            # Используем ILIKE для регистронезависимого поиска
            cur.execute(
                """
                SELECT 
                    e.name as company_name,
                    v.title as vacancy_name,
                    CASE 
                        WHEN v.salary_from IS NOT NULL AND v.salary_to IS NOT NULL 
                            THEN v.salary_from || '-' || v.salary_to 
                        WHEN v.salary_from IS NOT NULL 
                            THEN 'от ' || v.salary_from 
                        WHEN v.salary_to IS NOT NULL 
                            THEN 'до ' || v.salary_to 
                        ELSE 'не указана'
                    END as salary,
                    v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.id
                WHERE v.title ILIKE %s
                ORDER BY e.name, v.title
            """,
                (f"%{keyword}%",),
            )
            vacancies = cur.fetchall()
        conn.close()
        return vacancies

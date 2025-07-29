import psycopg2
from src.config import config


class DBManager:
    """Класс для управления данными в БД PostgreSQL"""

    def __init__(self, db_name, params):

        self.db_name = db_name
        self.params = params.copy()
        self.params['database'] = self.db_name

    def get_companies_and_vacancies_count(self):
        """Получает список компаний и количество вакансий"""
        conn = None
        try:
            conn = psycopg2.connect(**self.params)
            with conn.cursor() as cursor:
                cursor.execute("""
                       SELECT e.name, COUNT(v.id) as vacancies_count
                       FROM employers e
                       LEFT JOIN vacancies v ON e.id = v.employer_id
                       GROUP BY e.name
                       ORDER BY vacancies_count DESC
                   """)
                return cursor.fetchall()
        except Exception as e:
            print(f"Ошибка: {e}")
            return []
        finally:
            if conn:
                conn.close()


    def get_all_vacancies(self, db_name, params):
        """Получает список всех вакансий с указанием компании, названия, зарплаты и ссылки"""
        conn = psycopg2.connect(dbname=self.db_name, **self.params)

        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    e.name as company_name,
                    v.name as vacancy_name,
                    CASE 
                        WHEN v.salary_from IS NOT NULL AND v.salary_to IS NOT NULL 
                            THEN v.salary_from || '-' || v.salary_to || ' ' || v.currency
                        WHEN v.salary_from IS NOT NULL 
                            THEN 'от ' || v.salary_from || ' ' || v.currency
                        WHEN v.salary_to IS NOT NULL 
                            THEN 'до ' || v.salary_to || ' ' || v.currency
                        ELSE 'не указана'
                    END as salary,
                    v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.id
                ORDER BY company_name, vacancy_name
            """)

            vacancies = cur.fetchall()

        conn.close()

        return vacancies

    def get_avg_salary(self, db_name, params):
        """Получает среднюю зарплату по вакансиям (с учетом вилки зарплат)"""
        conn = psycopg2.connect(dbname=self.db_name, **self.params)

        with conn.cursor() as cur:
            # Вариант 1: Простое среднее между salary_from и salary_to
            cur.execute("""
                SELECT 
                    AVG((COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) / 2) as avg_salary,
                    currency
                FROM vacancies
                WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
                GROUP BY currency
            """)

            avg_salaries = cur.fetchall()

        conn.close()

        return avg_salaries

    def get_vacancies_with_higher_salary(self, db_name, params):
        """Получает список вакансий с зарплатой выше средней"""
        conn = psycopg2.connect(dbname=self.db_name, **self.params)

        with conn.cursor() as cur:
            # Сначала получаем среднюю зарплату
            cur.execute("""
                SELECT AVG(
                    CASE 
                        WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL 
                            THEN (salary_from + salary_to) / 2
                        WHEN salary_from IS NOT NULL 
                            THEN salary_from
                        WHEN salary_to IS NOT NULL 
                            THEN salary_to
                        ELSE NULL
                    END
                ) FROM vacancies
            """)
            avg_salary = cur.fetchone()[0]

            if not avg_salary:
                return []

            # Затем получаем вакансии с зарплатой выше средней
            cur.execute("""
                SELECT 
                    e.name as company_name,
                    v.name as vacancy_name,
                    CASE 
                        WHEN v.salary_from IS NOT NULL AND v.salary_to IS NOT NULL 
                            THEN v.salary_from || '-' || v.salary_to || ' ' || v.currency
                        WHEN v.salary_from IS NOT NULL 
                            THEN 'от ' || v.salary_from || ' ' || v.currency
                        WHEN v.salary_to IS NOT NULL 
                            THEN 'до ' || v.salary_to || ' ' || v.currency
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
            """, (avg_salary, avg_salary))

            vacancies = cur.fetchall()

        conn.close()

        return vacancies

    def get_vacancies_with_keyword(self, keyword):
        """Получает список вакансий, содержащих ключевое слово в названии"""
        conn = psycopg2.connect(dbname=self.db_name, **self.params)

        with conn.cursor() as cur:
            # Используем ILIKE для регистронезависимого поиска
            cur.execute("""
                SELECT 
                    e.name as company_name,
                    v.name as vacancy_name,
                    CASE 
                        WHEN v.salary_from IS NOT NULL AND v.salary_to IS NOT NULL 
                            THEN v.salary_from || '-' || v.salary_to || ' ' || v.currency
                        WHEN v.salary_from IS NOT NULL 
                            THEN 'от ' || v.salary_from || ' ' || v.currency
                        WHEN v.salary_to IS NOT NULL 
                            THEN 'до ' || v.salary_to || ' ' || v.currency
                        ELSE 'не указана'
                    END as salary,
                    v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.id
                WHERE v.name ILIKE %s
                ORDER BY e.name, v.name
            """, (f'%{keyword}%',))

            vacancies = cur.fetchall()

        conn.close()

        return vacancies


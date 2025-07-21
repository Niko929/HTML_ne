import psycopg2


def get_companies_and_vacancies_count(db_name, params):
    conn = psycopg2.connect(dbname=db_name, **params)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT e.name, e.vacancies_count 
            FROM employers e
            ORDER BY e.vacancies_count DESC
        """)

        companies = cur.fetchall()

    conn.close()

    return companies


def get_all_vacancies(db_name, params):
    """Получает список всех вакансий с указанием компании, названия, зарплаты и ссылки"""
    conn = psycopg2.connect(dbname=db_name, **params)

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


def get_avg_salary(db_name, params):
    """Получает среднюю зарплату по вакансиям (с учетом вилки зарплат)"""
    conn = psycopg2.connect(dbname=db_name, **params)

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


def get_vacancies_with_higher_salary(db_name, params):
    """Получает список вакансий с зарплатой выше средней"""
    conn = psycopg2.connect(dbname=db_name, **params)

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


def get_vacancies_with_keyword(db_name, params, keyword):
    """Получает список вакансий, содержащих ключевое слово в названии"""
    conn = psycopg2.connect(dbname=db_name, **params)

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
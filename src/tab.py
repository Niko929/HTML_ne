import psycopg2
from psycopg2.extras import execute_batch
from src.config import employer_ids
from src.hh import get_employers, get_vacancies_by_employer


def create_database(db_name, params):
    """Создание базы данных"""
    conn = psycopg2.connect(dbname="postgres", **params)
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        cursor.execute(f"CREATE DATABASE {db_name}")
        print(f"База данных {db_name} успешно создана")
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")
    finally:
        cursor.close()
        conn.close()


def create_tables(db_name, params):
    """Создание таблиц в базе данных"""
    conn = psycopg2.connect(dbname=db_name, **params)
    try:
        with conn:
            with conn.cursor() as cursor:
                # Таблица employers
                cursor.execute(
                    """
                    CREATE TABLE employers (
                        id VARCHAR(20) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        url VARCHAR(100),
                        description TEXT
                    )
                """
                )
                # Таблица vacancies
                cursor.execute(
                    """
                    CREATE TABLE vacancies (
                        id VARCHAR(20) PRIMARY KEY,
                        employer_id VARCHAR(20) REFERENCES employers(id),
                        title VARCHAR(100) NOT NULL,
                        salary_from INTEGER,
                        salary_to INTEGER,
                        url VARCHAR(100),
                        description TEXT
                    )
                """
                )
                print("Таблицы успешно созданы")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
    finally:
        conn.close()

def get_employers_vacancies(ed_id):
    """Получить данные о работодателях и их вакансиях"""
    employers = []
    vacancies = []
    for emp_id in employer_ids:
        try:
            employer_data = get_employers(ed_id)
            employer = {
                "id": employer_data["id"],
                "name": employer_data["name"],
                "url": (
                    employer_data["site_url"]
                    if employer_data.get("site_url")
                    else None
                ),
                "description": (
                    employer_data["description"]
                    if employer_data.get("description")
                    else None
                ),
            }
            employers.append(employer)

            vacancies_data = get_vacancies_by_employer(ed_id)
            for vac in vacancies_data:
                salary = vac.get("salary")
                salary_from = salary.get("from") if salary else None
                salary_to = salary.get("to") if salary else None

                vacancy = {
                    "id": vac["id"],
                    "employer_id": emp_id,
                    "title": vac["name"],
                    "salary_from": salary_from,
                    "salary_to": salary_to,
                    "url": vac["alternate_url"],
                    "description": (
                        vac["snippet"].get("requirement", "")
                        if vac.get("snippet")
                        else None
                    ),
                }
                vacancies.append(vacancy)

        except Exception as e:
            print(f"Ошибка при получении данных для работодателя {emp_id}: {e}")

    return employers, vacancies

def fill_tables(employers, vacancies, db_name, params):
    """Заполнение таблиц данными"""
    conn = psycopg2.connect(dbname=db_name, **params)

    try:
        with conn:
            with conn.cursor() as cursor:
                # Вставка данных о работодателях
                execute_batch(
                    cursor,
                    """
                       INSERT INTO employers (id, name, url, description)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT (id) DO NOTHING
                   """,
                    [
                        (e["id"], e["name"], e["alternate_url"], e["description"])
                        for e in employers
                    ],
                )
                # Вставка данных о вакансиях
                execute_batch(
                    cursor,
                    """
                       INSERT INTO vacancies (id, employer_id, title, salary_from, salary_to, url, description)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (id) DO NOTHING
                   """,
                    [
                        (
                            v["id"],
                            v["employer"]["id"],
                            v["name"],
                            v["salary"]["from"] if v['salary'] else None,
                            v["salary"]["to"] if v['salary'] else None,
                            v["alternate_url"],
                            v["snippet"].get("requirement"),
                        )
                        for v in vacancies
                    ],
                )

                print(
                    f"Добавлено {len(employers)} работодателей и {len(vacancies)} вакансий"
                )
    except Exception as e:
        print(f"Ошибка при заполнении таблиц: {e}")
    finally:
        conn.close()
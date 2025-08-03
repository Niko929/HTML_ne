import psycopg2
from psycopg2.extras import execute_batch
from src.tab import create_database, create_tables, fill_tables
from src.utils import DBManager
from src.config import config, employer_ids
from src.hh import get_employers, get_vacancies_by_employer

if __name__ == "__main__":
    db_name = "hh"
    params = config()
    #
    # create_database(db_name,params )
    # create_tables(db_name,params )
    #
    # # Создание таблицы
    # # id employer_id name salary url
    # # id name рабодататель связь с помощью references
    # employers = []
    # vacancies = []
    # for ed_id in employer_ids:
    #     employers_info = get_employers(ed_id)
    #     employers.append(employers_info)
    #     vacan = get_vacancies_by_employer(ed_id, per_page=100)
    #     vacancies.extend(vacan)
    # fill_tables(employers,vacancies,db_name,params)
    #

    db_manager = DBManager(db_name, params)

    print("\nКомпании и количество вакансий:")
    for company in db_manager.get_companies_and_vacancies_count():
        print(f"Компания {company[0]}: {company[1]} вакансия")

    print("\nВсе вакансия:")
    for company in db_manager.get_all_vacancies():
        print(f'''Компания : {company[0]}
Название вакансии: {company[1]} 
Зарплата: {company[2]}
Ссылка: {company[3]}
''')

    print("\nСредняя зарплата:")
    sdd = db_manager.get_avg_salary()
    print(sdd[0])

    print(f"\nвсе вакансии с ЗП более:{sdd}")
    for company in db_manager.get_vacancies_with_higher_salary():
        print(f'''Компания : {company[0]}
Название вакансии: {company[1]} 
Зарплата: {company[2]}
Ссылка: {company[3]}
        ''')

    keyword = str(input("Введите слово для поиска: "))
    print("\nВсе компания по ключевому слову:")
    for company in db_manager.get_vacancies_with_keyword(keyword):
        print(f"Компания {company[0]}: {company[1]} вакансия")

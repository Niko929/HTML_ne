from src.utils import (get_companies_and_vacancies_count, get_all_vacancies,
                       get_avg_salary, get_vacancies_with_higher_salary, get_vacancies_with_keyword)
from src.config import config
from src.hh import get_employers,get_vacancies_by_employer

def main():

    db_name = 'hh'
    params = config()
    search_keyword = str(input())
    nam_vaca = str(input())
    nomer_id = int(input())

    employers = get_employers(nam_vaca, per_page=10)
    vacan = get_vacancies_by_employer(nomer_id, per_page=10)




    # Создаем базу данных и сохраняем данные
    companies = get_companies_and_vacancies_count(db_name, params)
    vacancies = get_all_vacancies(db_name, params)
    avg_salaries = get_avg_salary(db_name, params)
    high_salary_vacancies = get_vacancies_with_higher_salary(db_name, params)
    keyword_vacancies = get_vacancies_with_keyword(db_name, params, search_keyword)



if __name__ == '__main__':
    main()
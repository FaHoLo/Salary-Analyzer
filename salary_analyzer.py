import requests
import os
from dotenv import load_dotenv
load_dotenv()
from terminaltables import AsciiTable


def main():
    print_both_sites_statistics_table()

def print_both_sites_statistics_table():
    languages = [
        'JavaScript',
        'Java',
        'Python',
        'Ruby',
        'PHP',
        'C',
        'C++',
        'C#',
        'Go',
        '1C',
        'TypeScript',
    ]
    print('HeadHunter:')
    headhunter_statistics = get_all_languages_statistics_hh(languages)
    print('SuperJob:')
    superjob_statistics = get_all_languages_statistics_sj(languages)
    print_the_table(headhunter_statistics, False)
    print()
    print_the_table(superjob_statistics, True)

def get_all_languages_statistics_hh(languages):
    languages_statistics = {language: get_language_statistics(language, False) for language in languages}
    return languages_statistics

def get_all_languages_statistics_sj(languages):
    languages_statistics = {language: get_language_statistics(language, True) for language in languages}
    return languages_statistics

def get_language_statistics(language, is_superjob):
    vacancies, vacancies_found = get_vacancies(language, is_superjob)
    average_salary, vacancies_processed = count_average_salary(vacancies, is_superjob)
    language_statistics = {
        'vacancies_found': vacancies_found,
        'vacancies_processed': vacancies_processed,
        'average_salary': average_salary,
    }
    return language_statistics

def get_vacancies(language, is_superjob):
    print(language)
    if language == 'C++': language = 'C%2B%2B' 
    if language == 'C#': language = 'C%23'
    if is_superjob:
        SUPERJOB_KEY = os.getenv('KEY')
        headers = {'X-Api-App-Id': f'{SUPERJOB_KEY}'}
        url = 'https://api.superjob.ru/2.0/vacancies/?keyword={}&town=4&catalogues=48&count=100{}'     
    else:
        request_parameters = 'text={}&specialization=1.221&describe_arguments=true&per_page=100&area=1&period=30&{}'
        headers = {}
        url = f'https://api.hh.ru/vacancies?{request_parameters}'
    page = 0
    pages_number = 1
    vacancies = []
    while page < pages_number:
        response = requests.get(url.format(language, f'page={page}'), headers=headers)
        response.raise_for_status()
        page_data = response.json()
        if is_superjob:
            vacancies_found = page_data['total']
            if vacancies_found == 0: return None, None
            pages_number = vacancies_found // 100 + 1
            if vacancies_found % 100 == 0: pages_number -= 1
            for vacancy in page_data['objects']:
                vacancies.append(vacancy)
        else:
            vacancies_found = page_data['found']
            pages_number = page_data['pages']
            for vacancy in page_data['items']:
                vacancies.append(vacancy)
        page += 1
        print(f'{page} of {pages_number} processed', )
    return vacancies, vacancies_found

def count_average_salary(vacancies, is_superjob):
    if vacancies == None: return None, None
    sum_of_salaries = 0
    number_of_salaries = 0
    for vacancy in vacancies:
        if is_superjob:
            current_salery = get_predict_rub_salary_sj(vacancy)
        else:
            current_salery = get_predict_rub_salary_hh(vacancy)
        if current_salery is None:
            pass
        else:
            sum_of_salaries = sum_of_salaries + current_salery
            number_of_salaries += 1
    if number_of_salaries == 0: return None, None
    average_salary = sum_of_salaries / number_of_salaries
    return int(average_salary), number_of_salaries

def get_predict_rub_salary_hh(vacancy):
    salary = vacancy['salary']
    if salary is None or salary['currency'] != 'RUR': return None
    predicted_salary = get_predict_salary(salary['from'],salary['to'])
    return predicted_salary

def get_predict_rub_salary_sj(vacancy):
    if vacancy['currency'] != 'rub': return None
    predicted_salary = get_predict_salary(vacancy['payment_from'],vacancy['payment_to'])
    return predicted_salary

def get_predict_salary(salary_from, salary_to):
    if salary_from == 0 and salary_to == 0:
        return None
    elif salary_from is None or salary_from == 0:
        predicted_salary = salary_to * 0.8
    elif salary_to is None or salary_from == 0:
        predicted_salary = salary_from * 1.2
    else:
        predicted_salary = (salary_from + salary_to) / 2
    predicted_salary = int(predicted_salary)
    if predicted_salary < 1000:
        predicted_salary = predicted_salary * 1000
    return predicted_salary

def print_the_table(languages_statistics, is_superjob):
    if is_superjob: 
        title = 'Super Job Moscow'
    else: 
        title = 'Head Hunter Moscow'
    table_data = [[
        'Язык программирования',
        'Вакансий найдено',
        'Вакансий обработано',
        'Средняя зарплата'
        ],
    ]
    for language, language_stats in languages_statistics.items():
        table_data.extend([[
            language,
            language_stats['vacancies_found'],
            language_stats['vacancies_processed'],
            language_stats['average_salary'],
        ]]) 
    table = AsciiTable(table_data, title)
    print(table.table)

if __name__ == '__main__':
    main()
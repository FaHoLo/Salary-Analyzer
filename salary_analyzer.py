import os

from dotenv import load_dotenv
import requests
from terminaltables import AsciiTable


def main():
    load_dotenv()
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
    headhunter_statistics = get_all_languages_statistics_hh(languages)
    superjob_statistics = get_all_languages_statistics_sj(languages)
    print_the_table(headhunter_statistics, 'Head Hunter Moscow')
    print()
    print_the_table(superjob_statistics, 'Super Job Moscow')


def get_all_languages_statistics_hh(languages):
    languages_statistics = {}
    for language in languages:
        request_arguments = collect_hh_request(language)
        languages_statistics[language] = get_language_statistics(language, request_arguments, process_page_hh, predict_rub_salary_hh)
    return languages_statistics


def collect_hh_request(language):
    request_arguments = {
        'headers': {},
        'payload': {
            'text': f'{language}',
            'specialization': 1.221,
            'describe_arguments': 'true',
            'per_page': 100,
            'area': 1,
            'period': 30,
        },
        'url': 'https://api.hh.ru/vacancies',
    }
    return request_arguments


def get_all_languages_statistics_sj(languages):
    languages_statistics = {}
    for language in languages:
        request_arguments = collect_sj_request(language)
        languages_statistics[language] = get_language_statistics(language, request_arguments, process_page_sj, predict_rub_salary_sj)
    return languages_statistics


def collect_sj_request(language):
    superjob_key = os.getenv('SUPERJOB_SECRET_KEY')
    request_arguments = {
        'headers': {'X-Api-App-Id': f'{superjob_key}'},
        'payload': {
            'keyword': f'{language}',
            'town': 4,
            'catalogues': 48,
            'count': 100,
        },
        'url': 'https://api.superjob.ru/2.0/vacancies/',
    }
    return request_arguments


def get_language_statistics(language, request_arguments, processing_page_function, predict_rub_salary_function):
    vacancies, vacancies_found = get_vacancies(language, request_arguments, processing_page_function)
    average_salary, vacancies_processed = count_average_salary(vacancies, predict_rub_salary_function)
    language_statistics = {
        'vacancies_found': vacancies_found,
        'vacancies_processed': vacancies_processed,
        'average_salary': average_salary,
    }
    return language_statistics


def get_vacancies(language, request_arguments, processing_page_function):
    headers = request_arguments['headers']
    payload = request_arguments['payload']
    url = request_arguments['url']
    page = 0
    pages_number = 1
    vacancies = []
    while page < pages_number:
        payload['page'] = page
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()
        page_data = response.json()
        vacancies_found, pages_number, vacancies = processing_page_function(page_data, vacancies)
        if not vacancies_found:
            return None, None
        page += 1
    return vacancies, vacancies_found


def process_page_hh(page_data, vacancies):
    vacancies_found = page_data['found']
    pages_number = page_data['pages']
    for vacancy in page_data['items']:
        vacancies.append(vacancy)
    return vacancies_found, pages_number, vacancies


def process_page_sj(page_data, vacancies):
    vacancies_found = page_data['total']
    if not vacancies_found:
        return None, None, None
    pages_number = vacancies_found // 100 + 1
    if vacancies_found % 100 == 0:
        pages_number -= 1
    for vacancy in page_data['objects']:
        vacancies.append(vacancy)
    return vacancies_found, pages_number, vacancies


def count_average_salary(vacancies, predict_rub_salary_function):
    if vacancies is None:
        return None, None
    sum_of_salaries = 0
    number_of_salaries = 0
    for vacancy in vacancies:
        current_salery = predict_rub_salary_function(vacancy)
        if current_salery is None:
            pass
        else:
            sum_of_salaries = sum_of_salaries + current_salery
            number_of_salaries += 1
    if number_of_salaries == 0:
        return None, None
    average_salary = sum_of_salaries / number_of_salaries
    return int(average_salary), number_of_salaries


def predict_rub_salary_hh(vacancy):
    salary = vacancy['salary']
    if salary is None or salary['currency'] != 'RUR':
        return None
    predicted_salary = predict_salary(salary['from'], salary['to'])
    return predicted_salary


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] != 'rub':
        return None
    predicted_salary = predict_salary(vacancy['payment_from'], vacancy['payment_to'])
    return predicted_salary


def predict_salary(salary_from, salary_to):
    if not salary_from and not salary_to:
        return None
    elif not salary_from:
        predicted_salary = salary_to * 0.8
    elif not salary_to:
        predicted_salary = salary_from * 1.2
    else:
        predicted_salary = (salary_from + salary_to) / 2
    predicted_salary = int(predicted_salary)
    if predicted_salary < 1000:
        predicted_salary = predicted_salary * 1000
    return predicted_salary


def print_the_table(languages_statistics, title):
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

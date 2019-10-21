from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
from selenium.webdriver.common.keys import Keys
from random import randint
from bs4 import BeautifulSoup
import pandas as pd
import os
import inspect


def get_credentials():
    return {
        'email': 'andreibarboni@gmail.com',
        'password': 'fofolete22'
    }


def get_params(ies, year):
    return {
        'input': 'D:\\LOCAL\\CODE\\LINKED_IN\\tmp\\' + ies + '\\output\\' + year + '.txt',
        'output': os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '\\output\\' + str(year) + '\\' + ies + '.txt'#{
            # 'valid': os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '\\output\\' + str(year) + '\\valid\\' + ies + '.txt',
            # 'invalid': os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '\\output\\' + str(year) + '\\invalid\\' + ies + '.txt'
        #}
    }


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--incognito")

    return webdriver.Chrome('C:/Python36/chromedriver.exe', chrome_options=options)


def by_id(driver, element, list=False):
    return driver.find_elements_by_id(element) if list else driver.find_element_by_id(element)


def by_class(driver, element, list=False):
    return driver.find_elements_by_class_name(element) if list else driver.find_element_by_class_name(element)


def by_name(driver, element, list=False):
    return driver.find_elements_by_name(element) if list else driver.find_element_by_name(element)


def by_css(driver, element, list=False):
    return driver.find_elements_by_css_selector('.' + element.replace(' ', '.')) if list else driver.find_element_by_css_selector('.' + element.replace(' ', '.'))


def get_main_page_params():
    return {
        'url': 'https://www.glassdoor.com.br/Sal%C3%A1rios/index.htm',
        'keyword_search_field': 'KeywordSearch',
        'location_search_field': 'LocationSearch',
        'hero_search_button': 'HeroSearchButton',
        '': '',
    }


def get_search_page_params():
    return {
        'keyword_search_field': 'sc.keyword',
        'location_search_field': 'sc.location',
        'hero_search_button': 'HeroSearchButton',
        'popular_companies': {
            'employer_name': 'salaryRow__JobInfoStyle__employerName',
            'salary_samples_amount': 'salaryRow__JobInfoStyle__jobCount minor',
            'salary': 'salaryRow__JobInfoStyle__meanBasePay common__formFactorHelpers__showHH',
            'min_max_salary': 'salaryRow__JobInfoStyle__range common__formFactorHelpers__showHH'
        }
    }


def get_df_columns():
    return ['ies', 'employer_name', 'position', 'salary_samples_amount', 'salary', 'avg_salary', 'min_salary', 'max_salary']


def get_pre_df_columns():
    return ['ies', 'employer_name', 'position', 'salary_samples_amount', 'salary', 'min_max_salary']


def random_sleep():
    sleep(randint(1, 3))


def login(driver):
    driver.get('https://www.glassdoor.com.br/index.htm')

    # random_sleep()

    by_class(driver, 'locked-home-sign-in').click()

    # random_sleep()

    by_name(driver, 'username').send_keys(get_credentials()['email'])
    by_name(driver, 'password').send_keys(get_credentials()['password'])
    by_name(driver, 'password').send_keys(Keys.RETURN)


def get_digits(value):
    result = ''
    for char in value:
        if char.isdigit():
            result += char
    return result


def format_salary(value):
    if 'mil' in value:
        return get_digits(value) + '000'
    elif 'milhões' in value or 'milhão' in value:
        return get_digits(value) + '000000'
    return get_digits(value)


def get_avg_min_max_salaries(data):
    min_salary = format_salary(str(data).split('-')[0].lstrip().rstrip())
    max_salary = format_salary(str(data).split('-')[1].lstrip().rstrip())
    avg_salary = int(int(min_salary) + (int(max_salary) - int(min_salary))/2)
    return [str(avg_salary), str(min_salary), str(max_salary)]


def transform(content):
    soup = BeautifulSoup(content, "lxml")
    content = {}
    raw_data = get_search_page_params()['popular_companies']
    for pos in raw_data:
        temp_result = []
        for link in soup.findAll('div', {'class': raw_data[pos]}):
            temp_result.append(link.text)
        content[pos] = temp_result
    return content


def build_data_frame(raw_data, year, ies, position):
    df = pd.DataFrame(columns=get_df_columns())

    if not os.path.isfile(get_params(ies, year)['output']):
        pd.DataFrame.to_csv(df, get_params(ies, year)['output'], sep='|', decimal=',', encoding='UTF-8', header=True, index=False)

    for i in range(0, len(raw_data['employer_name'])):
        for column in get_pre_df_columns():
            if column == 'min_max_salary':
                salaries = get_avg_min_max_salaries(raw_data[column][i].split(':')[1])
                df.at[i, 'avg_salary'] = salaries[0]
                df.at[i, 'min_salary'] = salaries[1]
                df.at[i, 'max_salary'] = salaries[2]
            elif column == 'ies':
                df.at[i, 'ies'] = ies
            elif column == 'position':
                df.at[i, 'position'] = position
            else:
                data = str(raw_data[column][i]).lstrip().rstrip()
                if column in ['salary_samples_amount', 'salary']:
                    data = get_digits(data)
                df.at[i, column] = data

    if len(df) == 0:
        df.at[0, 'ies'] = ies
        df.at[0, 'position'] = position

    db = pd.read_csv(get_params(ies, year)['output'], sep='|', decimal=',', encoding='UTF-8', low_memory=False, error_bad_lines=False)
    db = db.append(df, ignore_index=True)
    pd.DataFrame.to_csv(db, get_params(ies, year)['output'], sep='|', decimal=',', encoding='UTF-8', header=True, index=False)


def get_location():
    return {
        'USJT': 'São Paulo, São Paulo',
        'UNIMONTE': 'Santos, São Paulo',
        'UNA': 'Belo Horizonte, Minas Gerais',
        'UNISOCIESC': 'Santa Catarina',
        'UNIBH': 'Belo Horizonte',
    }


def extract(ies, position):
    if not bool(position):
        return

    driver = get_driver()
    login(driver)

    main_page_data = get_main_page_params()

    random_sleep()

    driver.get(main_page_data['url'])

    random_sleep()

    by_id(driver, main_page_data['keyword_search_field']).send_keys(position)
    by_id(driver, main_page_data['location_search_field']).clear()
    by_id(driver, main_page_data['location_search_field']).send_keys(get_location()[ies])
    by_id(driver, main_page_data['hero_search_button']).click()

    random_sleep()

    driver.switch_to_window(driver.window_handles[1])

    return driver.page_source


def get_positions_list(ies, year):
    db = pd.read_csv(get_params(ies, year)['input'], sep='|', decimal=',', encoding='UTF-8', low_memory=False, error_bad_lines=False)
    db = db.loc[db['extraction_type'] == 'work']
    db.drop_duplicates(subset=['position'], inplace=True)

    if os.path.isfile(get_params(ies, year)['output']):
        df_tmp = pd.read_csv(get_params(ies, year)['output'], sep='|', decimal=',', encoding='UTF-8', low_memory=False, error_bad_lines=False)
        df_tmp.drop_duplicates(subset=['position'], inplace=True)
        db = db.loc[~db['position'].isin(df_tmp['position'].tolist())]
        del df_tmp

    db.fillna('', inplace=True)
    return db['position'].tolist()


def run_nelson(ies):
    # for ies in ['USJT', 'UNIMONTE', 'UNA', 'UNISOCIESC', 'UNIBH']:
    for year in ['2019']:
        for position in get_positions_list(ies, year):
            print('IES ' + ies + ' | ' + str(year) + ' | Cargo: ' + str(position))
            try:
                content = extract(ies, position)
                content = transform(content)
                build_data_frame(content, year, ies, position)
            except Exception as ex:
                print(position + ' ' + str(ex))
                continue


for ies in ['USJT', 'UNIMONTE', 'UNA', 'UNISOCIESC', 'UNIBH']:
    run_nelson(ies)


# if __name__ == '__main__':
#     from multiprocessing import Pool
#     ieses = ['USJT', 'UNIMONTE', 'UNA', 'UNISOCIESC', 'UNIBH']
#     pool_inep = Pool(len(ieses))
#     for ies in ieses:
#         pool_inep.apply_async(run_nelson, [ies])
#     pool_inep.close()
#     pool_inep.join()

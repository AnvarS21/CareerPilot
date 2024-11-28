from bs4 import BeautifulSoup
import lxml
import requests

from job.constants import DEV_KG_URL
from job.parser.base_parser import BaseParser


class DevKG(BaseParser):

    def get_response_text(self):
        text = ''
        for page in range(1, 9):
            response = requests.get(DEV_KG_URL+str(page))
            text += response.text

        return text

    def search_vacancies(self, vacancy: str):
        result = []

        text = self.get_response_text()
        soup = BeautifulSoup(text, 'lxml')
        vacancies_html = soup.find_all(name='article', class_='item')
        for vacancy_html in vacancies_html:
            position = vacancy_html.find(name='div', class_='jobs-item-field position').text.replace('Должность',
                                                                                                '').strip()
            if vacancy in position.lower():
                company = vacancy_html.find(name='div', class_='jobs-item-field company').text.replace('Компания',
                                                                                              '').strip()
                link = "https://devkg.com" + vacancy_html.find(name='a', class_='link').get('href')
                salary = vacancy_html.find(name='div', class_='jobs-item-field price').text.replace('Оклад', '').strip()
                job_type = vacancy_html.find(name='div', class_='jobs-item-field type').text.replace('Тип', '').strip()
                result.append({
                    'title': position,
                    'company': company,
                    'link': link,
                    'salary': salary,
                    'job_type': job_type,
                    'status': 'Новая'
                })

        return result
from typing import Dict, List

import requests

from job.constants import HEAD_HUNTER_URL, KYRGYZSTAN_AREA_CODE
from job.parser.base_parser import BaseParser


class HhParser(BaseParser):
    def get_response_text(self) -> str:
        pass

    def search_vacancies(self, vacancy: str) -> List[Dict]:
        result = []
        vacancies = []
        for i in range(1, 11):
            page_vacancies_list = requests.get(url=HEAD_HUNTER_URL, params={
                                                                'text': vacancy,
                                                                'area':KYRGYZSTAN_AREA_CODE,
                                                                'per_page':'10',
                                                                'page': i
                                                            }).json().get('items')
            vacancies.extend(page_vacancies_list)

        for vacancy in vacancies:
            salary = vacancy.get('salary') or {}
            result.append({
                'title': vacancy.get('name'),
                'company': vacancy.get('employer', {}).get('name'),
                'link': vacancy.get('alternate_url'),
                'salary': f"{salary.get('from')} - {salary.get('to')}",
                'job_type': vacancy.get('schedule', {}).get('name'),
                'status': 'Новая'
            })

        return result

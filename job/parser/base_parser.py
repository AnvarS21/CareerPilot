from abc import ABC, abstractmethod

from typing import List, Dict


class BaseParser(ABC):

    @abstractmethod
    def get_response_text(self) -> str:
        pass

    @abstractmethod
    def search_vacancies(self, vacancy: str) -> List[Dict]:
        pass

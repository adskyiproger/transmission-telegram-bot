from bs4 import BeautifulSoup
from models.SearchBase import SearchBase
from typing import List

class SearchRUTOR(SearchBase):
    TRACKER_NAME = 'rutor'
    TRACKER_URL = "http://rutor.info"
    TRACKER_SEARCH_URL_TPL = "/search/0/0/000/0/"

    def convert_date(self, date: str):
        _date = date.split("\xa0")
        months = {
            "Янв": "01",
            "Фев": "02",
            "Мар": "03",
            "Апр": "04",
            "Май": "05",
            "Июн": "06",
            "Июл": "07",
            "Авг": "08",
            "Сен": "09",
            "Окт": "10",
            "Ноя": "11",
            "Дек": "12"
        }
        if len(_date) == 3:
            yyyy = f"20{_date[2]}"
            mm = months[_date[1]]
            dd = _date[0]
            return f"{yyyy}-{mm}-{dd}"
        else:
            self.log.warn("Date was not converted: %s", date)
            return date

    def search(self, search_string: str) -> List:
        """Search data on the web"""

        _data = self.get_data(search_string).select('div#index > table > tr')
        self.log.info("Found %s posts", len(_data) - 1)

        posts = []
        for row in _data[1:]:
            _cols = row.select('td')
            TITLE = _cols[1].select('a')[2].text
            INFO = _cols[1].select('a')[2].get('href')
            DL = _cols[1].select('a')[1].get('href')
            SIZE = _cols[3].text if len(_cols) == 5 else _cols[2].text
            DATE = self.convert_date(_cols[0].text)
            if len(_cols) == 5:
                SEEDS = _cols[4].text.split("\xa0")[1]
                LEACH = _cols[4].text.split("\xa0")[3]
            else:
                SEEDS = LEACH = 0
            self.log.debug("COL Title:"+TITLE+" L:"+str(INFO)+" DL:"+str(DL)+" S:"+str(SIZE)+" D:"+str(DATE))

            posts.append({
                'tracker': self.TRACKER_NAME,
                'title': TITLE.replace(r'<', ''),
                'info': "{0}/{1}".format(self.TRACKER_URL, INFO),
                'dl': DL,
                'size': SIZE,
                'date': DATE,
                'seed': SEEDS,
                'leach': LEACH})
        return posts

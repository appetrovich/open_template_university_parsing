import re
import os
import time
import random
import requests
import textract 
import PyPDF2  #можно использовать эту библиотеку, если с textract проблемы

from bs4 import BeautifulSoup
from base_parser import BaseParser


#Здесь примеры нескольких парсеров блоков 

#Парсинг блока https://guestbook.spbu.ru/vse-obrashcheniya.html
class Guestbook_parser(BaseParser):
    def __init__(self, pages, start_page=0, time_sleep=False):
        super().__init__()
        self.url = 'https://guestbook.spbu.ru/vse-obrashcheniya.html' #Стартовая страница данного блока
        self.pages = pages #Количество страниц (по 30 ссылок на каждой) (Навигация по страницам блока)
        self.start_page = start_page #Стартовая страница для парсинга
        self.time_sleep = time_sleep #Не обязательно, только если вдруг сайт ругается на частые запросы
        self.topic_block = 'guestbook' #Название парсера блока (желательно выбирать короткое и интуитивно понятное)

    #Сбор ссылок на вопросы с главной страницы
    def parse_urls(self):
        all_pages_urls = [] #Все ссылки, которые будем парсить
        cur_url = self.url 
        for i in range(self.start_page + 1, self.start_page + self.pages + 1):
            src = self.read_site(cur_url) #Чтение страницы
            soup = BeautifulSoup(src, "lxml") #Скармливаем в BS4
            one_page_urls = [item.find_next().get("href") for item in \
                            soup.find_all("td", class_= "list-title")] #Собираем все ссылки на одной странице
            all_pages_urls.extend(one_page_urls) #Добавляем в общий пул ссылок
            cur_url = self.url + f'?start={30*i}' #Переход к следующей странице
            if self.time_sleep is True:
                time.sleep(random.randrange(1, 3))

        res = ['https://guestbook.spbu.ru' + url for url in all_pages_urls] #Формируем все ссылки, которые будем парсить
        return res


    #Парсинг текста сайтов c ответами на вопросы
    def parse_text(self, url):
        src = self.read_site(url)
        soup = BeautifulSoup(src, "lxml")

        full_text = soup.find_all("p")[1:-4] #Парсинг параграфов 
        header = soup.find(class_="title").text #Парсинг заголовка 
        
        res = header + self.headers_sep + " ".join([paragraph.text for paragraph in full_text]).replace("\n", " ") #Текст, который будет в столбце "context"
        res = self.regex_cleaning(res) #Очищаем этот текст от лишних символов
        
        #Определение даты публикации страницы
        try:
            public_date = soup.find("time").get("datetime") 
        except AttributeError:
            public_date = None
        
        #Добавление timesleep при необходимости
        if self.time_sleep is True:
            time.sleep(random.randrange(1, 3))
        return header, res, public_date #Всегда возвращаем 3 аргумента


#Парсинг блока https://spbu.ru/postupayushchim/programms/
class Edu_programms_parser(BaseParser):
    def __init__(self, time_sleep=False):
        super().__init__()
        self.url = 'https://spbu.ru/postupayushchim/programms/'
        self.pages = ['bakalavriat', 'magistratura', 'aspirantura', 'ordinatura',\
                      'dopolnitelnyeprogrammy', 'obshcheeobrazovanie', 'dovuzovskoeobrazovanie'] #Здесь страницы уже в виде списка
        self.time_sleep = time_sleep 
        self.topic_block = 'edu_programms'    

    #Сбор ссылок с главной страницы раздела
    def parse_urls(self):
        all_pages_urls = []

        for page in self.pages: 
            cur_url = self.url + page + '?view=table'
            src = self.read_site(cur_url)
            soup = BeautifulSoup(src, "lxml")
            one_page_urls = [item.get("href") for item in \
                    soup.find_all("a", class_="table__row")]
            all_pages_urls.extend(one_page_urls)

            if self.time_sleep is True:
                time.sleep(random.randrange(1, 3))

        res = ['https://spbu.ru' + url for url in all_pages_urls]
        return res

    #Парсинг текста сайтов
    def parse_text(self, url):
        src = self.read_site(url)
        soup = BeautifulSoup(src, "lxml")

        header = soup.find("h1").text
        language = soup.find("p", class_ = "program-headline__note").text.strip() + "; "
        headline_info = ",".join([item.text for item in soup.find_all(class_="program-headline__info")]) + "; "
        apply_conditions = ", ".join([item.text for item in soup.find_all("div", class_="program-stats__group")]) + ". "

        block_title = soup.find_all("div", class_= "collapse__bt")
        block_text = soup.find_all("div", class_= "collapse__content")
        block_content = ". ".join([title.text.strip() + ": " + paragraph.text.strip() + ". " for title, paragraph in zip(block_title, block_text)]).replace("\n", ", ")
        
        res = header + self.headers_sep  + language + headline_info + apply_conditions + block_content
        res = self.regex_cleaning(res)

        public_date = None

        if self.time_sleep is True:
            time.sleep(random.randrange(1, 3))
        return header, res, public_date   


#Парсинг блока https://spbu.ru/postupayushchim/calendar/
class Calendar_parser(BaseParser):
    def __init__(self, time_sleep=False):
        super().__init__()
        self.url = 'https://spbu.ru/postupayushchim/calendar/'
        self.pages = ['bakalavriat', 'magistratura', 'aspirantura', 'ordinatura', \
                      'dopolnitelnyeprogrammy', 'obshcheeobrazovanie', 'dovuzovskoeobrazovanie']
        self.time_sleep = time_sleep 
        self.topic_block = 'calendar'          

    #Сбор ссылок с главной страницы раздела
    def parse_urls(self):
        all_pages_urls = []

        for page in self.pages: 
            cur_url = self.url + page
            src = self.read_site(cur_url)
            soup = BeautifulSoup(src, "lxml")
            one_page_urls = soup.find("ul", class_="menu-tab") \
                            .find("li", class_ = "menu-item menu-item--act") \
                            .find("a").get("href")
     
            all_pages_urls.extend([one_page_urls])
            if self.time_sleep is True:
                time.sleep(random.randrange(1, 3))

        res = ['https://spbu.ru' + url for url in all_pages_urls]
        return res  

    #Парсинг текста сайтов
    def parse_text(self, url):
        src = self.read_site(url)
        soup = BeautifulSoup(src, "lxml")
        edu_group = soup.find("ul", class_="menu-tab") \
                    .find("li", class_ = "menu-item menu-item--act") \
                    .find("a").text
        header = f"{soup.find('h1', class_ = 'header-h1').text}" + f" ({edu_group})" 


        all_dates = [item.text for item in soup.find_all("div", class_ = ["list-calendar__date col-sm-2 list-calendar__date--mark", "list-calendar__date col-sm-2"])]
        dates_info = [item.text for item in soup.find_all("div", class_ = "list-calendar__title col-sm-9 col-lg-7")]
        calendar_data = ". ".join([date + " - " + info for date, info in zip(all_dates, dates_info)]).replace("\n", " ")

        res = header + self.headers_sep + calendar_data
        res = self.regex_cleaning(res)

        public_date = None

        if self.time_sleep is True:
            time.sleep(random.randrange(1, 3))
        return header, res, public_date  


#Парсинг блока https://abiturient.spbu.ru/news/
class Spbu_news_parser(BaseParser):
    def __init__(self, pages, time_sleep=False):
        super().__init__()
        self.url = 'https://abiturient.spbu.ru/news/'
        self.pages = pages #Количество страниц (по 24 ссылки на каждой)
        self.time_sleep = time_sleep 
        self.topic_block = 'news'
        self.min_text_size = 400

    #Сбор ссылок на вопросы с главной страницы
    def parse_urls(self):
        all_pages_urls = []
        cur_url = self.url
        for i in range(1, self.pages + 1):
            src = self.read_site(cur_url)
            soup = BeautifulSoup(src, "lxml")
            one_page_urls = [item.get("href") for item in \
                             soup.find_all("a", class_ = "news-card__text")]
            all_pages_urls.extend(one_page_urls)
            cur_url = self.url + f'?PAGEN_1={i}'
            if self.time_sleep is True:
                time.sleep(random.randrange(1, 3))

        res = ['https://abiturient.spbu.ru' + url for url in all_pages_urls]
        return res

    #Парсинг текста сайтов c ответами на вопросы
    def parse_text(self, url):
        src = self.read_site(url)
        soup = BeautifulSoup(src, "lxml")

        header = soup.find("h1", class_ = "title").text 
        date = soup.find("div", class_ = "card-footer card-footer--reversed").text + "."
        news = " ".join([item.text for item in soup.find_all("div", class_ = "text-content")]).replace("\n", " ")
        
        res = header + self.headers_sep + date + news
        res = self.regex_cleaning(res)

        public_date = None
        
        if self.time_sleep is True:
            time.sleep(random.randrange(1, 3))
        return header, res, public_date


            
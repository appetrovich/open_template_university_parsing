import re
import os
import time
import random
import requests
import textract
import PyPDF2 #jn

from config import config

from bs4 import BeautifulSoup

class BaseParser:
    def __init__(self):
        self.headers_sep = " - заголовок страницы;; " #ОБЯЗАТЕЛЬНЫЙ ЭЛЕМЕНТ (он отделяет заголовок страницы и его контент)

    @staticmethod
    def read_site(url):
        headers = {
            "User-Agent": "ваши данные",
            "Accept": "ваши данные",
            "Accept-Language": 'ru-RU,ru'
        }
        req = requests.get(url, headers=headers)
        src = req.text
        return src

    # Удаление лишних символов и фраз
    @staticmethod
    def regex_cleaning(text):
        text = re.sub('\xa0', ' ', text)
        text = re.sub('\\s+', ' ', text)
        text = re.sub('\\s{2,}', ' ', text)
        text = re.sub(',\\s{1,},', ',', text)
        text = re.sub(' ,', ',', text)
        text = re.sub(':,', ':', text)
        text = re.sub(',,', ',', text)
        text = re.sub(' \.', '.', text)
        text = re.sub('\.,', '.', text)
        text = re.sub('\.\.', '. ', text)
        text = re.sub('%20', '', text)
        text = re.sub(
            'Адрес электронной почты защищен от спам-ботов. Для просмотра адреса в вашем браузере должен быть включен Javascript.',
            '', text)
        return text.strip()

    # Очистка pdf документа от шумовых символов
    @staticmethod
    def pdf_cleaning(text):
        text = re.sub(r'[|\^\x0c\xa0\n]', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        text.strip()
        return text

    # Чтение и сохранение pdf документа
    @staticmethod
    def load_and_parse_pdf(url, topic_block, title, replace=False):
        headers = {
            "Accept": "ваши данные",
            "User-Agent": "ваши данные"
        }
        # Подготовка заголовка для файла
        title = BaseParser.pdf_cleaning(title)
        title = re.sub(r'/', ' ', title).replace(" ", "_")

        # Проверяем существование директории с pdf файлами
        dir_path = f'data/{topic_block}'
        dirExist = os.path.exists(dir_path)
        if not dirExist:
            os.makedirs(dir_path)
            # Проверка на существование файла в директории
        file_path = dir_path + f'/{title}.pdf'
        fileExist = os.path.exists(file_path)

        # Скачиваем ли заново отсутствующий pdf файл
        if replace is False:
            if not fileExist:
                response = requests.get(url, headers=headers)
                with open(file_path, 'wb') as f:
                    f.write(response.content)
        else:
            response = requests.get(url, headers=headers)
            with open(file_path, 'wb') as f:
                f.write(response.content)
                # Извлечение текста из pdf документа
        text = textract.process(file_path)
        text = text.decode('utf-8')
        # Очистка документа от шумовых символов
        text = BaseParser.pdf_cleaning(text)
        # Проверка на корректность полученного текста из pdf
        if len(re.sub('[^а-яА-ЯёЁ]', '', text)) < 500:
            text = 'empty'

        title = title.replace("_", " ")
        return title, text


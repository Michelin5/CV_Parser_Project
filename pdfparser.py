from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import io
import pdfplumber
import PyPDF2

import spacy
from spacy.matcher import Matcher

from nltk.corpus import stopwords

import re

import os

import phonenumbers

import docx2txt

import pprint

from ai_client import OpenAIClient


def _extract_links(file_path):
    """
        Извлекает ссылки на социальные сети и другие платформы из текста.
        """
    if file_path.endswith('.pdf'):
        PDFFile = open(f"{file_path}", 'rb')

        PDF = PyPDF2.PdfReader(PDFFile)
        pages = len(PDF.pages)
        key = '/Annots'
        uri = '/URI'
        ank = '/A'

        relevant_links = []

        for page in range(pages):
            # print("Current Page: {}".format(page))
            pageSliced = PDF.pages[page]
            pageObject = pageSliced.get_object()
            if key in pageObject.keys():
                ann = pageObject[key]
                for a in ann:
                    u = a.get_object()
                    if uri in u[ank].keys():
                        if not u[ank][uri].startswith('tel:'):
                            relevant_links.append(u[ank][uri])
        return relevant_links
    return []


def _extract_text_from_pdf(pdf_path):
    """
    Извлекает текст из PDF файла.
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text() + '\n'
    # print(text)
    return text


def extract_text_from_doc(doc_path):
    """
    Helper function to extract plain text from .doc or .docx files

    :param doc_path: path to .doc or .docx file to be extracted
    :return: string of extracted text
    """
    temp = docx2txt.process(doc_path)
    text = [line.replace('\t', ' ') for line in temp.split('\n') if line]
    return ' '.join(text)


class CVParser:
    def __init__(self, file_path):
        nlp = spacy.load('en_core_web_sm')
        self.matcher = Matcher(nlp.vocab)
        self.file_path = file_path
        self.text = self._extract_text()
        self.nlp_text = nlp(self.text)

    def _extract_text(self):
        """
        Извлекает текст из файла.
        """
        text = ''
        if self.file_path.endswith('.pdf'):
            # two variants
            text = _extract_text_from_pdf(self.file_path)
            # for page in extract_text_from_pdf(self.file_path):
            #     text += ' ' + page
        elif self.file_path.endswith('.docx') or self.file_path.endswith('.doc'):
            text = extract_text_from_doc(self.file_path)
        return text

    def extract_entity_sections(self):
        """
        Helper function to extract all the raw text from sections of resume

        :return: dictionary of entities
        """

        RESUME_SECTIONS = [
            'accomplishments',
            'experience',
            'education',
            'technologies',
            'interests',
            'projects',
            'professional experience',
            'publications',
            'skills',
            'achievements'
        ]

        text_split = [i.strip() for i in self.text.split('\n')]
        # sections_in_resume = [i for i in text_split if i.lower() in sections]
        entities = {}
        key = False
        for phrase in text_split:
            if len(phrase) == 1:
                p_key = phrase
            else:
                p_key = set(phrase.lower().split()) & set(RESUME_SECTIONS)
            try:
                p_key = list(p_key)[0]
            except IndexError:
                pass
            if p_key in RESUME_SECTIONS:
                entities[p_key] = []
                key = p_key
            elif key and phrase.strip():
                entities[key].append(phrase)

        for x in entities.keys():
            entities[x] = '\n'.join(entities[x])

        return entities

    def extract_name(self):
        # First name and Last name are always Proper Nouns
        pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]

        self.matcher.add('NAME', [pattern], on_match=None)

        matches = self.matcher(self.nlp_text)

        for match_id, start, end in matches:
            span = self.nlp_text[start:end]
            return span.text

    def extract_email(self):
        """
        Извлекает email из текста.
        """
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        match = re.search(email_pattern, self.text)

        if match:
            return match.group(0)
        else:
            links = _extract_links(self.file_path)
            for x in links:
                if x.startswith('mailto:'):
                    return x.lstrip('mailto:')
        return None

    def extract_phone_number(self):
        """
        Извлекает номер телефона из текста.
        """
        for match in phonenumbers.PhoneNumberMatcher(self.text, "US"):
            return phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        return None

    def extract_links(self):
        """
            Извлекает ссылки на социальные сети и другие платформы из текста.
            """
        return _extract_links(self.file_path)

    def summarize(self):
        try:
            openai_client = OpenAIClient()

            message = f'Есть текст резюме, грамотно и структурированно сделай пересказ этого резюме, изложив основные ' \
                      f'аспекты: опыт работы, образование, технические навыки, заслуги, общая инфомация и тд (чисто по ' \
                      f'фактам, без художественных дополнений, максимально сжато, в свободном формате (не просто ' \
                      f'списком)): {self.text} '

            user_prompt = message.strip()

            response = openai_client.get_response(user_prompt)

            # print(response)

            return response
        except Exception:
            return 'Ошибка :('

    def parse(self):
        """
        Парсит резюме и возвращает извлечённые данные в виде словаря.
        """
        return {
            'Name': self.extract_name(),
            'Email': self.extract_email(),
            'Phone': self.extract_phone_number(),
            'Relevant links': self.extract_links(),
            'Entities': self.extract_entity_sections(),
            'Summary': self.summarize()
        }


# Пример использования
if __name__ == "__main__":
    parser = CVParser('examples/resume.pdf')
    parsed_data = parser.parse()

    for key, value in parsed_data.items():
        print(f"{key}:")
        pprint.pprint(value)
        print('--------------------')

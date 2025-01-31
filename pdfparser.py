import pdfplumber
import re
import phonenumbers


class CVParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.text = self._extract_text_from_pdf()

    def _extract_text_from_pdf(self):
        """
        Извлекает текст из PDF файла.
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text() + '\n'
        return text

    def extract_name(self):
        """
        Извлекает имя из текста резюме, анализируя первые строки.
        Предполагается, что имя — это два или три слова, начинающиеся с заглавной буквы.
        """
        name_pattern = r'^[A-Z][a-z]+\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)?'
        lines = self.text.split('\n')[:3]
        for line in lines:
            match = re.match(name_pattern, line.strip())
            if match:
                return match.group(0)
        return None

    def extract_email(self):
        """
        Извлекает email из текста.
        """
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        match = re.search(email_pattern, self.text)
        return match.group(0) if match else None

    def extract_phone_number(self):
        """
        Извлекает номер телефона из текста.
        """
        for match in phonenumbers.PhoneNumberMatcher(self.text, "US"):
            return phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        return None

    def extract_education(self):
        """
        Извлекает информацию об образовании из текста.
        """
        education_keywords = ['university', 'college', 'institute', 'school']
        lines = self.text.lower().split('\n')
        education_info = [line.strip() for line in lines if any(keyword in line for keyword in education_keywords)]
        return education_info

    def extract_social_links(self):
        """
        Ищет ссылки на соцсети в тексте.
        """
        social_patterns = {
            'LinkedIn': r'(https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+)',
            'GitHub': r'(https?://(www\.)?github\.com/[a-zA-Z0-9_-]+)',
            'Twitter': r'(https?://(www\.)?twitter\.com/[a-zA-Z0-9_-]+)',
            'Facebook': r'(https?://(www\.)?facebook\.com/[a-zA-Z0-9_.-]+)',
            'Personal Website': r'(https?://[a-zA-Z0-9_-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9_-]+)?)',
        }

        links = {}
        for platform, pattern in social_patterns.items():
            match = re.search(pattern, self.text)
            if match:
                links[platform] = match.group(0)

        return links

    def parse(self):
        """
        Парсит резюме и возвращает извлечённые данные в виде словаря.
        """
        return {
            'Name': self.extract_name(),
            'Email': self.extract_email(),
            'Phone': self.extract_phone_number(),
            'Education': self.extract_education(),
            'Social Links': self.extract_social_links(),
        }


# Пример использования
if __name__ == "__main__":
    pdf_file = "examples/resume.pdf"
    parser = CVParser(pdf_file)
    parsed_data = parser.parse()

    for key, value in parsed_data.items():
        print(f"{key}: {value}")

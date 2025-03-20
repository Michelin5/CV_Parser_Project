import pdfplumber
import re
import phonenumbers
import os


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
        print(text)
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
        education = []
        current_edu = {}
        in_education_section = False
        processing_edu = False

        # Паттерны
        institution_pattern = r'^([A-Z][a-zA-Z\s,&.-]+?)(?=\s*(?:\(|\d{4}|[A-Z]{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))'
        date_range_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\s*[–—-]\s*(?:Expected\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})'
        degree_pattern = r'(Bachelor|Master|PhD|B\.?[AS]\.?|M\.?[AS]\.?)\s+of\s+[\w\s]+'
        gpa_pattern = r'(?:GPA\s*[:]?|Grade\s*Point\s*Average\s*[:]?)\s*(\d\.\d{1,2}\s*[out of\s]*[\d\.]*)'

        lines = [line.strip() for line in self.text.split('\n')]

        for i, line in enumerate(lines):
            if re.fullmatch(r'^\s*education\s*$', line, re.IGNORECASE):
                in_education_section = True
                continue
            elif re.fullmatch(r'^\s*(experience|skills|projects|work history)\s*$', line, re.IGNORECASE):
                in_education_section = False

            if in_education_section and line:
                if not processing_edu:
                    institution_match = re.match(institution_pattern, line)
                    if institution_match:
                        current_edu['institution'] = institution_match.group(1).strip()
                        line = line.replace(institution_match.group(1), '', 1).strip()
                        processing_edu = True

                if processing_edu:
                    if not current_edu.get('dates'):
                        date_match = re.search(date_range_pattern, line)
                        if date_match:
                            current_edu['dates'] = date_match.group(1).replace('–', '-').strip()
                            line = line.replace(date_match.group(1), '', 1).strip()

                    if not current_edu.get('degree'):
                        degree_match = re.search(degree_pattern, line, re.I)
                        if degree_match:
                            current_edu['degree'] = degree_match.group(0).strip()
                            line = line.replace(degree_match.group(0), '', 1).strip()

                    if not current_edu.get('gpa'):
                        gpa_match = re.search(gpa_pattern, line, re.I)
                        if gpa_match:
                            current_edu['gpa'] = gpa_match.group(1).strip()
                            line = line.replace(gpa_match.group(0), '', 1).strip()

                    if i < len(lines) - 1:
                        next_line = lines[i + 1]

                        if not current_edu.get('gpa'):
                            gpa_match_next = re.search(gpa_pattern, next_line, re.I)
                            if gpa_match_next:
                                current_edu['gpa'] = gpa_match_next.group(1).strip()
                                lines[i + 1] = next_line.replace(gpa_match_next.group(0), '', 1).strip()

                        if not current_edu.get('degree'):
                            degree_match_next = re.search(degree_pattern, next_line, re.I)
                            if degree_match_next:
                                current_edu['degree'] = degree_match_next.group(0).strip()
                                lines[i + 1] = next_line.replace(degree_match_next.group(0), '', 1).strip()

                    save_condition = (
                            current_edu.get('institution') and
                            (current_edu.get('dates') or current_edu.get('degree'))
                    )

                    if save_condition:
                        if 'degree' in current_edu:
                            current_edu['degree'] = re.sub(r'\s*GPA.*$', '', current_edu['degree']).strip()
                        education.append(current_edu.copy())
                        current_edu.clear()
                        processing_edu = False

        return education

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
    for pdf_file in os.listdir('examples'):
        print('------------------------------------')
    parser = CVParser('examples/'+'CV.pdf')
    parsed_data = parser.parse()

    for key, value in parsed_data.items():
        print(f"{key}: {value}")

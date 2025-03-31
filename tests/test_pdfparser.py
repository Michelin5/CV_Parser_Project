import pytest
from pathlib import Path
from unittest.mock import Mock
import spacy
from pdfparser import CVParser, _extract_links


@pytest.fixture(scope='session')
def nlp():
    return spacy.load('en_core_web_sm')


def test_extract_name(nlp):
    test_resume = """
    John Doe
    Senior Software Engineer
    Experience:
    - Developed systems at Google
    """

    class MockParser:
        def __init__(self):
            self.nlp = nlp
            self.text = test_resume
            self.nlp_text = self.nlp(self.text)
            self.matcher = spacy.matcher.Matcher(self.nlp.vocab)

    parser = MockParser()
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
    parser.matcher.add('NAME', [pattern])

    name = None
    matches = parser.matcher(parser.nlp_text)
    for _, start, end in matches:
        span = parser.nlp_text[start:end]
        name = span.text
        break

    assert name == "John Doe"


def test_extract_email(sample_pdf_path):
    parser = CVParser(sample_pdf_path)
    email = parser.extract_email()
    assert email and '@' in email


def test_phone_number_extraction():
    test_text = "Contact: +79151234567"
    parser = CVParser("dummy_path")
    parser.text = test_text
    phone = parser.extract_phone_number()
    assert phone == "+7 915 123-45-67"


def test_links_extraction(sample_pdf_path):
    links = _extract_links(sample_pdf_path)
    assert isinstance(links, list)
    if links:
        assert all(link.startswith('http') or link.startswith('mailto') for link in links)


def test_full_parse(sample_pdf_path, mock_openai):
    parser = CVParser(sample_pdf_path)
    result = parser.parse()

    assert isinstance(result, dict)
    required_keys = {'Name', 'Email', 'Phone', 'Relevant links', 'Entities', 'Summary'}
    assert required_keys.issubset(result.keys())

    assert isinstance(result['Name'], (str, type(None)))
    assert isinstance(result['Summary'], str)

    mock_openai.assert_called_once()
import pytest
import os
from pathlib import Path

@pytest.fixture
def sample_pdf_path():
    return str(Path("examples/CV.pdf").absolute())

@pytest.fixture
def sample_docx_path():
    return str(Path("examples/CV.docx").absolute())

@pytest.fixture
def mock_openai(mocker):
    return mocker.patch(
        'pdfparser.OpenAIClient.get_response',
        return_value="Mocked summary text"
    )
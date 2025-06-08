import zipfile
from pathlib import Path

import pytest


@pytest.fixture
def read_simplified_melies() -> str:
    """
    A simplified version of the Georges Melies page from Wikipedia.

    the file is zipped to save space in the repository.

    Returns:
        str: The HTML content of the Beethoven page.
    """
    current_dir = Path(__file__).parent
    zip_path = current_dir / "test_html/simplified_melies.html.zip"

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        files = zip_ref.namelist()
        for file in files:
            if file == "simplified_melies.html":
                print(f"Extracting {file} from the zip file.")
                with zip_ref.open(file) as html_file:
                    return html_file.read().decode("utf-8")

import zipfile
from pathlib import Path

import pytest


@pytest.fixture
def read_beethoven_html() -> str:
    """
    Reads the HTML content of the Beethoven page from the test data directory.

    the file is zipped to save space in the repository.

    Returns:
        str: The HTML content of the Beethoven page.
    """
    current_dir = Path(__file__).parent
    zip_path = current_dir / "wikipedia_html/Ludwig_van_Beethoven.html.zip"

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        files = zip_ref.namelist()
        for file in files:
            if file == "Ludwig_van_Beethoven.html":
                print(f"Extracting {file} from the zip file.")
                with zip_ref.open(file) as html_file:
                    return html_file.read().decode("utf-8")


@pytest.fixture
def read_melies_html() -> str:
    """
    Reads the HTML content of the Beethoven page from the test data directory.

    the file is zipped to save space in the repository.

    Returns:
        str: The HTML content of the Beethoven page.
    """
    current_dir = Path(__file__).parent
    zip_path = current_dir / "wikipedia_html/Georges_Melies.html.zip"

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        files = zip_ref.namelist()
        for file in files:
            if file == "Georges_Melies.html":
                print(f"Extracting {file} from the zip file.")
                with zip_ref.open(file) as html_file:
                    return html_file.read().decode("utf-8")

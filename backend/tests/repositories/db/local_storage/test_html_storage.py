from pathlib import Path

import pytest

from src.entities.movie import Movie
from src.entities.person import Person
from src.repositories.db.local_storage.html_storage import LocalTextStorage

current_dir = Path(__file__).parent


@pytest.fixture(autouse=True, scope="function")
def cleanup_directory():
    # Cleanup before test
    storage = LocalTextStorage(
        path=current_dir, entity_type=Movie
    ).persistence_directory
    for child in storage.rglob("*"):
        if child.is_file():
            child.unlink()

    storage = LocalTextStorage(
        path=current_dir, entity_type=Person
    ).persistence_directory
    for child in storage.rglob("*"):
        if child.is_file():
            child.unlink()

    yield
    storage = LocalTextStorage(
        path=current_dir, entity_type=Movie
    ).persistence_directory
    for child in storage.rglob("*"):
        if child.is_file():
            child.unlink()

    storage = LocalTextStorage(
        path=current_dir, entity_type=Person
    ).persistence_directory
    for child in storage.rglob("*"):
        if child.is_file():
            child.unlink()


def test_local_text_storage_init():
    # Given

    storage = LocalTextStorage(path=current_dir, entity_type=Movie)

    # When
    storage_path = storage.persistence_directory

    # Then
    assert storage_path == current_dir / "html" / "movie"
    assert storage_path.exists()


def test_local_text_storage_insert():
    # Given
    storage = LocalTextStorage(path=current_dir, entity_type=Movie)
    content_id = "test"
    content = "<html><body><h1>Test</h1></body></html>"

    # When
    storage.insert(content_id, content)

    # Then
    path = storage.persistence_directory / f"{content_id}.html"
    assert path.exists()
    with open(path, "r") as f:
        assert f.read() == content


def test_local_text_storage_insert_existing_path():
    # Given
    storage = LocalTextStorage(path=current_dir, entity_type=Movie)
    content_id = "test"
    content = "<html><body><h1>Test</h1></body></html>"
    path = storage.persistence_directory / f"{content_id}.html"

    # Create a file to simulate existing path
    with open(path, "w") as f:
        f.write("Existing content")

    # When
    storage.insert(content_id, content)

    # Then
    assert path.exists()
    with open(path, "r") as f:
        assert f.read() == content


def test_local_text_storage_select():
    # Given
    storage = LocalTextStorage(path=current_dir, entity_type=Movie)
    content_id = "test"
    content = "<html><body><h1>Test</h1></body></html>"
    storage.insert(content_id, content)

    # When
    result = storage.select(content_id)

    # Then
    assert result == content


def test_local_text_storage_select_non_existent():
    # Given
    storage = LocalTextStorage(path=current_dir, entity_type=Movie)
    content_id = "non_existent"

    # When
    result = storage.select(content_id)

    # Then
    assert result is None


def test_local_text_storage_scan():

    # Given
    storage = LocalTextStorage(path=current_dir, entity_type=Movie)
    content_id_1 = "test1"
    content_1 = "<html><body><h1>Test 1</h1></body></html>"
    content_id_2 = "test2"
    content_2 = "<html><body><h1>Test 2</h1></body></html>"
    storage.insert(content_id_1, content_1)
    storage.insert(content_id_2, content_2)

    # When
    results = list(storage.scan())

    # Then
    assert len(results) == 2
    assert (content_id_1, content_1) in results
    assert (content_id_2, content_2) in results


def test_local_text_storage_scan_returns_correct_content_id():
    # Given
    storage = LocalTextStorage(path=current_dir, entity_type=Movie)
    content_id_1 = "test1"
    content_1 = "<html><body><h1>Test 1</h1></body></html>"
    storage.insert(content_id_1, content_1)

    # When
    results = list(storage.scan())

    # Then
    assert len(results) == 1
    assert results[0][0] == content_id_1
    assert results[0][1] == content_1


def test_local_text_storage_scan_no_files():
    # Given
    storage = LocalTextStorage(path=current_dir, entity_type=Movie)

    # When
    results = list(storage.scan())

    # Then
    assert len(results) == 0


def test_local_text_storage_scan_with_pattern():
    # Given
    storage = LocalTextStorage(path=current_dir, entity_type=Movie)
    content_id_1 = "test1"
    content_1 = "<html><body><h1>Test 1</h1></body></html>"
    content_id_2 = "haha"
    content_2 = "<html><body><h1>Test 2</h1></body></html>"
    storage.insert(content_id_1, content_1)
    storage.insert(content_id_2, content_2)

    # When
    results = list(storage.scan(file_pattern="test?.html"))

    # Then
    assert len(results) == 1
    assert (content_id_1, content_1) in results

from pathlib import Path

import pytest

from src.entities.film import Film
from src.repositories.storage.html_storage import LocalTextStorage

current_dir = Path(__file__).parent


def test_local_text_storage_init():
    # Given

    storage = LocalTextStorage[Film](path=current_dir)

    # When
    storage_path = storage.path

    # Then
    assert storage_path == current_dir / "html" / "film"
    assert storage_path.exists()

    # Teardown
    storage_path.rmdir()
    Path(current_dir / "html").rmdir()


def test_local_text_storage_bad_init():
    # Given

    current_dir

    # When
    # Then
    with pytest.raises(ValueError):
        LocalTextStorage(path=current_dir)


def test_local_text_storage_insert():
    # Given
    storage = LocalTextStorage[Film](path=current_dir)
    content_id = "test"
    content = "<html><body><h1>Test</h1></body></html>"

    # When
    storage.insert(content_id, content)

    # Then
    path = storage.path / f"{content_id}.html"
    assert path.exists()
    with open(path, "r") as f:
        assert f.read() == content

    # Teardown
    path.unlink()
    storage.path.rmdir()
    Path(current_dir / "html").rmdir()


def test_local_text_storage_insert_existing_path():
    # Given
    storage = LocalTextStorage[Film](path=current_dir)
    content_id = "test"
    content = "<html><body><h1>Test</h1></body></html>"
    path = storage.path / f"{content_id}.html"

    # Create a file to simulate existing path
    with open(path, "w") as f:
        f.write("Existing content")

    # When
    storage.insert(content_id, content)

    # Then
    assert path.exists()
    with open(path, "r") as f:
        assert f.read() == content

    # Teardown
    path.unlink()
    storage.path.rmdir()
    Path(current_dir / "html").rmdir()


def test_local_text_storage_select():
    # Given
    storage = LocalTextStorage[Film](path=current_dir)
    content_id = "test"
    content = "<html><body><h1>Test</h1></body></html>"
    storage.insert(content_id, content)

    # When
    result = storage.select(content_id)

    # Then
    assert result == content

    # Teardown
    path = storage.path / f"{content_id}.html"
    path.unlink()
    storage.path.rmdir()
    Path(current_dir / "html").rmdir()


def test_local_text_storage_select_non_existent():
    # Given
    storage = LocalTextStorage[Film](path=current_dir)
    content_id = "non_existent"

    # When
    result = storage.select(content_id)

    # Then
    assert result is None

    # Teardown
    storage.path.rmdir()
    Path(current_dir / "html").rmdir()


def test_local_text_storage_scan():
    # Given
    storage = LocalTextStorage[Film](path=current_dir)
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
    assert content_1 in results
    assert content_2 in results

    # Teardown
    Path(storage.path / f"{content_id_1}.html").unlink()
    Path(storage.path / f"{content_id_2}.html").unlink()
    storage.path.rmdir()
    Path(current_dir / "html").rmdir()


def test_local_text_storage_scan_no_files():
    # Given
    storage = LocalTextStorage[Film](path=current_dir)

    # When
    results = list(storage.scan())

    # Then
    assert len(results) == 0

    # Teardown
    storage.path.rmdir()
    Path(current_dir / "html").rmdir()


def test_local_text_storage_scan_with_pattern():
    # Given
    storage = LocalTextStorage[Film](path=current_dir)
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
    assert content_1 in results

    # Teardown
    Path(storage.path / f"{content_id_1}.html").unlink()
    Path(storage.path / f"{content_id_2}.html").unlink()
    storage.path.rmdir()
    Path(current_dir / "html").rmdir()

from pathlib import Path

from src.interfaces.extractor import PageLink
from src.repositories.html_parser.wikipedia_extractor import WikipediaExtractor
from src.settings import WikiTOCPageConfig


def test_extract_links_from_table():
    """
    Test the extraction of film links from a Wikipedia page.
    """

    # given
    extractor = WikipediaExtractor()

    # Mock HTML content
    html_content = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <table class="wikitable">
                <tr>
                    <th>Titre</th>
                </tr>
                <tr>
                    <td><a href="./Film_Title">Film Title</a></td>
                </tr>
                <tr>
                    <td><a href="./Other_Film_Title">Other Film Title</a></td>
                </tr>
            </table>
        </body>
    </html>
    """

    config = WikiTOCPageConfig(
        page_id="My TOC Page",
        toc_content_type="film",
        toc_css_selector=".wikitable td:nth-child(1)",
    )

    # Expected output
    expected_output = [
        PageLink(
            page_title="Film Title",
            page_id="Film_Title",
            content_type="film",
        ),
        PageLink(
            page_title="Other Film Title",
            page_id="Other_Film_Title",
            content_type="film",
        ),
    ]

    # Call the function to test
    result = extractor.retrieve_inner_links(html_content, config)

    # Assert the result
    assert all(
        item in result for item in expected_output
    ), f"Expected {expected_output}, but got {result}"
    assert all(item in expected_output for item in result)


def test_extract_links_with_css_selector():
    """
    target only the column with persons
    """

    # given
    extractor = WikipediaExtractor()

    config = WikiTOCPageConfig(
        page_id="My TOC Page",
        toc_content_type="person",
        toc_css_selector=".wikitable td:nth-child(2)",
    )

    # Mock HTML content
    html_content = """
    <table class="wikitable">
        <tr>
            <th>Titre</th>
            <th>Réalisateur</th>
        </tr>
        <tr>
            <td><a href="./Film_Title">Film Title</a></td>
            <td><a rel="mw:WikiLink" href="./Lucien_Nonguet" title="Lucien Nonguet" id="mwFw">Lucien Nonguet</a></td>
        </tr>
        <tr>
            <td><a href="./Film_Title">Film Title</a></td>
            <td><a rel="mw:WikiLink" href="./toto" title="Toto"> Toto </a></td>
        </tr>
    </table>
    """

    # Expected output
    expected_output = [
        PageLink(
            page_title="Lucien Nonguet",
            page_id="Lucien_Nonguet",
            content_type="person",
        ),
        PageLink(
            page_title="Toto",
            page_id="toto",
            content_type="person",
        ),
    ]

    # Call the function to test
    result = extractor.retrieve_inner_links(html_content, config)

    # Assert the result
    assert all(
        item in result for item in expected_output
    ), f"Expected {expected_output}, but got {result}"
    assert all(item in expected_output for item in result)


def test_dedup_extract_links():

    # given
    extractor = WikipediaExtractor()

    config = WikiTOCPageConfig(
        page_id="My TOC Page",
        toc_content_type="person",
        toc_css_selector=".wikitable td:nth-child(2)",
    )

    # Mock HTML content
    html_content = """
    <table class="wikitable">
        <tr>
            <th>Titre</th>
            <th>Réalisateur</th>
        </tr>
        <tr>
            <td><a href="./Film_Title">Film Title</a></td>
            <td><a rel="mw:WikiLink" href="./Lucien_Nonguet" title="Lucien Nonguet" id="mwFw">Lucien Nonguet</a></td>
        </tr>
        <tr>
            <td><a href="./Film_Title">Film Title</a></td>
            <td><a rel="mw:WikiLink" href="./Lucien_Nonguet" title="Toto"> Toto </a></td>
        </tr>
    </table>
    """

    # Expected output
    expected_output = [
        PageLink(
            page_title="Lucien Nonguet",
            page_id="Lucien_Nonguet",
            content_type="person",
        ),
    ]

    # Call the function to test
    result = extractor.retrieve_inner_links(html_content, config)

    # Assert the result
    assert result == expected_output, f"Expected {expected_output}, but got {result}"


def test_extract_links_with_no_links():
    """
    Test the extraction of links when there are no links in the HTML content.
    """

    # given
    extractor = WikipediaExtractor()

    config = WikiTOCPageConfig(
        page_id="My TOC Page",
        toc_content_type="person",
    )

    # Mock HTML content
    html_content = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <table class="wikitable">
                <tr>
                    <th>Titre</th>
                </tr>
                <tr>
                    <td>No Links Here</td>
                </tr>
            </table>
        </body>
    </html>
    """

    # Expected output
    expected_output = []

    # Call the function to test
    result = extractor.retrieve_inner_links(html_content, config)

    # Assert the result
    assert result == expected_output, f"Expected {expected_output}, but got {result}"


def test_extract_links_excludes_external_links():
    """
    Test the extraction of links when there are external links in the HTML content.
    """

    # given
    extractor = WikipediaExtractor()

    config = WikiTOCPageConfig(
        page_id="My TOC Page",
        toc_content_type="film",
    )

    # Mock HTML content
    html_content = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <table class="wikitable">
                <tr>
                    <th>Titre</th>
                </tr>
                <tr>
                    <td><a href="./Film_Title">Film Title</a></td>
                </tr>
                <tr>
                    <td><a href="http://www.external-link.com">External Link</a></td>
                </tr>
            </table>
        </body>
    </html>
    """

    # Expected output
    expected_output = [
        PageLink(
            page_title="Film Title",
            page_id="Film_Title",
            content_type="film",
        ),
    ]

    # Call the function to test
    result = extractor.retrieve_inner_links(html_content, config)

    # Assert the result
    assert all(
        item in result for item in expected_output
    ), f"Expected {expected_output}, but got {result}"
    assert all(item in expected_output for item in result)


def test_extract_links_excludes_non_existing_pages():
    """
    Test the extraction of links when there are non-existing pages in the HTML content.
    """

    # given
    extractor = WikipediaExtractor()

    config = WikiTOCPageConfig(
        page_id="My TOC Page",
        toc_content_type="film",
    )

    # Mock HTML content
    html_content = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <table class="wikitable">
                <tr>
                    <th>Titre</th>
                </tr>
                <tr>
                    <td><a href="./Film_Title">Film Title</a></td>
                </tr>
                <tr>
                    <td><a href="./Non_Existing_Page?action=edit" title="Non Existing Page">Non Existing Page</a></td>
                </tr>
            </table>
        </body>
    </html>
    """

    # Expected output
    expected_output = [
        PageLink(
            page_title="Film Title",
            page_id="Film_Title",
            content_type="film",
        ),
    ]

    # Call the function to test
    result = extractor.retrieve_inner_links(html_content, config)

    # Assert the result
    assert all(
        item in result for item in expected_output
    ), f"Expected {expected_output}, but got {result}"
    assert all(item in expected_output for item in result)


def test_parse_info_table():

    # given
    current_dir = Path(__file__).parent
    html_file = current_dir / "wikipedia_html/Beethoven.html"
    html_content = html_file.read_text(encoding="utf-8")

    semantic = WikipediaExtractor()

    # when
    info_box = semantic.retrieve_infoboxes(html_content)

    # then
    assert info_box is not None
    assert len(info_box) > 0

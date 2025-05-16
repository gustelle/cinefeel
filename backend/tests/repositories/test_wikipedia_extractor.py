from src.interfaces.link_extractor import WikiPageLink
from src.repositories.wikipedia_extractor import WikipediaLinkExtractor


def test_extract_links_from_table():
    """
    Test the extraction of film links from a Wikipedia page.
    """

    # given
    extractor = WikipediaLinkExtractor()

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
                    <th>Réalisateur</th>
                </tr>
                <tr>
                    <td><a href="./Film_Title">Film Title</a></td>
                    <td><a rel="mw:WikiLink" href="./Lucien_Nonguet" title="Lucien Nonguet" id="mwFw">Lucien Nonguet</a></td>
                </tr>
            </table>
        </body>
    </html>
    """

    # Expected output
    expected_output = [
        WikiPageLink(
            page_title="Film Title",
            page_id="Film_Title",
        ),
        WikiPageLink(
            page_title="Lucien Nonguet",
            page_id="Lucien_Nonguet",
        ),
    ]

    # Call the function to test
    result = extractor.retrieve_inner_links(html_content)

    # Assert the result
    assert all(
        item in result for item in expected_output
    ), f"Expected {expected_output}, but got {result}"
    assert all(item in expected_output for item in result)


def test_extract_links_from_table_target_only_col():
    """
    target only the column with persons
    """

    # given
    extractor = WikipediaLinkExtractor()

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
        WikiPageLink(
            page_title="Lucien Nonguet",
            page_id="Lucien_Nonguet",
        ),
        WikiPageLink(
            page_title="Toto",
            page_id="toto",
        ),
    ]

    # Call the function to test
    result = extractor.retrieve_inner_links(
        html_content, css_selector="td:nth-child(2)"
    )

    # Assert the result
    assert all(
        item in result for item in expected_output
    ), f"Expected {expected_output}, but got {result}"
    assert all(item in expected_output for item in result)


def test_dedup_extract_links():

    # given
    extractor = WikipediaLinkExtractor()

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
        WikiPageLink(
            page_title="Lucien Nonguet",
            page_id="Lucien_Nonguet",
        ),
    ]

    # Call the function to test
    result = extractor.retrieve_inner_links(
        html_content, css_selector="td:nth-child(2)"
    )

    # Assert the result
    assert result == expected_output, f"Expected {expected_output}, but got {result}"

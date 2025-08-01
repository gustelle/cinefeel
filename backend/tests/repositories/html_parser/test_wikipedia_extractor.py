import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from src.interfaces.info_retriever import PageLink, RetrievalError
from src.repositories.html_parser.wikipedia_info_retriever import WikipediaParser
from src.settings import TableOfContents


def test_extract_links_from_table():
    """
    Test the extraction of film links from a Wikipedia page.
    """

    # given
    extractor = WikipediaParser()

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

    config = TableOfContents(
        page_id="My TOC Page",
        entity_type="Movie",
        permalinks_selector=".wikitable td:nth-child(1)",
    )

    # Expected output
    expected_output = [
        PageLink(
            page_title="Film Title",
            page_id="Film_Title",
            entity_type="Movie",
        ),
        PageLink(
            page_title="Other Film Title",
            page_id="Other_Film_Title",
            entity_type="Movie",
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
    extractor = WikipediaParser()

    config = TableOfContents(
        page_id="My TOC Page",
        entity_type="Person",
        permalinks_selector=".wikitable td:nth-child(2)",
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
            entity_type="Person",
        ),
        PageLink(
            page_title="Toto",
            page_id="toto",
            entity_type="Person",
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
    extractor = WikipediaParser()

    config = TableOfContents(
        page_id="My TOC Page",
        entity_type="Person",
        permalinks_selector=".wikitable td:nth-child(2)",
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
            entity_type="Person",
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
    extractor = WikipediaParser()

    config = TableOfContents(
        page_id="My TOC Page",
        entity_type="Person",
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
    extractor = WikipediaParser()

    config = TableOfContents(
        page_id="My TOC Page",
        entity_type="Movie",
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
            entity_type="Movie",
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
    extractor = WikipediaParser()

    config = TableOfContents(
        page_id="My TOC Page",
        entity_type="Movie",
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
            entity_type="Movie",
        ),
    ]

    # Call the function to test
    result = extractor.retrieve_inner_links(html_content, config)

    # Assert the result
    assert all(
        item in result for item in expected_output
    ), f"Expected {expected_output}, but got {result}"
    assert all(item in expected_output for item in result)


def test_retrieve_infobox(read_beethoven_html):

    # given

    semantic = WikipediaParser()

    # when
    info_box = semantic.retrieve_infobox(read_beethoven_html)

    # then
    assert info_box is not None
    assert len(info_box.content) > 0


def test_retrieve_infobox_return_table(read_beethoven_html):

    # given

    semantic = WikipediaParser()

    # when
    info_box = semantic.retrieve_infobox(read_beethoven_html, format_as="table")

    # then
    assert info_box is not None
    soup = BeautifulSoup(info_box.content, "html.parser")
    assert soup.table is not None, "Content is not in table format"


def test_retrieve_infobox_return_list(read_beethoven_html):

    # given

    semantic = WikipediaParser()

    # when
    info_box = semantic.retrieve_infobox(read_beethoven_html)

    # then
    assert info_box is not None
    soup = BeautifulSoup(info_box.content, "html.parser")
    assert soup.ul is not None, "Content is not in list format"


def test_retrieve_infobox_section_title(read_beethoven_html):

    # given

    semantic = WikipediaParser()

    # when
    info_box = semantic.retrieve_infobox(read_beethoven_html)

    # then
    assert info_box.title == "Données clés"


def test_retrieve_permalink_from_canonical(read_beethoven_html):

    # given

    semantic = WikipediaParser()

    # when
    permalink = semantic.retrieve_permalink(read_beethoven_html)

    # then
    assert str(permalink) == "https://fr.wikipedia.org/wiki/Ludwig_van_Beethoven"


def test_retrieve_permalink_from_isVersionOf():

    # given
    current_dir = Path(__file__).parent
    html_file = current_dir / "test_html/permalink_no_canonical.html"
    html_content = html_file.read_text(encoding="utf-8")

    semantic = WikipediaParser()

    # when
    permalink = semantic.retrieve_permalink(html_content)

    # then
    assert str(permalink) == "https://fr.wikipedia.org/wiki/test"


def test_retrieve_permalink_raises():

    # given
    current_dir = Path(__file__).parent
    html_file = current_dir / "test_html/no_permalink.html"
    html_content = html_file.read_text(encoding="utf-8")

    semantic = WikipediaParser()

    # when / then
    with pytest.raises(RetrievalError, match="Permalink not found"):
        semantic.retrieve_permalink(html_content)


def test_retrieve_title(read_beethoven_html):
    # given

    semantic = WikipediaParser()

    # when
    title = semantic.retrieve_title(read_beethoven_html)

    # then
    assert title == "Ludwig van Beethoven"


def test_retrieve_title_raises():
    # given
    current_dir = Path(__file__).parent
    html_file = current_dir / "test_html/no_page_title.html"
    html_content = html_file.read_text(encoding="utf-8")

    semantic = WikipediaParser()

    # when / then
    with pytest.raises(RetrievalError, match="Title not found"):
        semantic.retrieve_title(html_content)


def test_retrieve_orphan_paragraphs():
    # given
    html = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <p>This is an orphan paragraph before the first section.</p>
            <section>
                <h2>First Section</h2>
                <p>This is the first section content.</p>
                <h2>Second Section</h2>
                <p>This is the second section content.</p>
                <p>This is an orphan paragraph after the last section.</p>
            </section>
        </body>
    """
    semantic = WikipediaParser()

    # when
    orphan_section = semantic.retrieve_orphan_paragraphs(html)

    # then
    assert orphan_section is not None
    assert orphan_section.title == "Introduction"
    assert (
        "This is an orphan paragraph before the first section" in orphan_section.content
    )


def test_retrieve_orphan_paragraphs_works_with_divs():
    # given
    html = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <p>This is an orphan paragraph before the first section.</p>
            <div>
                <h2>First Section</h2>
                <p>This is the first section content.</p>
                <h2>Second Section</h2>
                <p>This is the second section content.</p>
                <p>This is an orphan paragraph after the last section.</p>
            </div>
        </body>
    """
    semantic = WikipediaParser()

    # when
    orphan_section = semantic.retrieve_orphan_paragraphs(html)

    # then
    assert orphan_section is not None
    assert orphan_section.title == "Introduction"
    assert (
        "This is an orphan paragraph before the first section" in orphan_section.content
    )


def test_retrieve_media(read_beethoven_html):
    # given
    semantic = WikipediaParser()

    # when
    media = semantic.retrieve_media(read_beethoven_html)

    # then

    assert media is not None
    assert len(media) > 0
    assert (
        len(list(filter(lambda m: m.media_type == "image", media))) > 0
    ), "No image media found"
    assert (
        len(list(filter(lambda m: m.media_type == "audio", media))) > 0
    ), "No video media found"


def test_retrieve_media_exclude_pattern(sample_infobox):
    # given
    semantic = WikipediaParser()

    # when
    pattern = r".+pencil\.svg.+"
    media = semantic.retrieve_media(sample_infobox, exclude_pattern=pattern)

    # then

    assert media is not None
    assert len(media) > 0
    assert (
        len(list(filter(lambda m: m.media_type == "image", media))) > 0
    ), "No image media found"

    assert not any(
        re.match(pattern, str(m.src), re.I) for m in media  # type: ignore
    ), "Excluded media found in the result"


def test_orphan_paragraphs_having_media():
    # given
    html = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <p>This is an orphan paragraph with media.</p>
            <img src="https://example.com/image.jpg" alt="Test Image">
            <audio src="https://example.com/audio.mp3" controls></audio>
        </body>
    </html>
    """
    semantic = WikipediaParser()

    # when
    orphan_section = semantic.retrieve_orphan_paragraphs(html)

    # then
    assert orphan_section is not None
    assert orphan_section.title == "Introduction"
    assert "This is an orphan paragraph with media" in orphan_section.content
    assert (
        len(orphan_section.media) == 2
    ), "Expected 2 media items in the orphan section"


def test_orphan_paragraphs_exclude_flag_media():
    # given
    html = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <p>This is an orphan paragraph with media.</p>
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Flag_of_France_%281976%E2%80%932020%29.svg/40px-Flag_of_France_%281976%E2%80%932020%29.svg.png" alt="Test Image">
            <audio src="https://example.com/audio.mp3" controls></audio>
        </body>
    </html>
    """
    semantic = WikipediaParser()

    # when
    orphan_section = semantic.retrieve_orphan_paragraphs(html)

    # then
    assert not any(media.media_type == "image" for media in orphan_section.media)


def test_infobox_with_media(sample_infobox):
    # given
    exclude_pattern = r".+pencil\.svg.+"
    semantic = WikipediaParser()

    # when
    info_box = semantic.retrieve_infobox(sample_infobox)

    # then
    assert info_box is not None
    assert len(info_box.media) > 0, "No media found in the infobox"
    assert all(
        media.media_type == "image" for media in info_box.media
    ), "Not all media are images"

    assert not any(
        re.match(exclude_pattern, str(m.src), re.I) for m in info_box.media
    ), "Excluded media found in the result"


def test_infobox_info_icon_excluded(sample_infobox):
    # given
    exclude_pattern = r"40px-Info_Simple\.svg\.png"
    semantic = WikipediaParser()

    # when
    info_box = semantic.retrieve_infobox(sample_infobox, format_as="simple")

    # then
    assert info_box is not None
    assert len(info_box.content) > 0, "No content found in the infobox"
    assert not any(
        re.match(exclude_pattern, str(m.src), re.I) for m in info_box.media
    ), "Excluded media found in the result"

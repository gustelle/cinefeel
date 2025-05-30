from bs4 import BeautifulSoup

from src.repositories.ml.html_simplifier import HTMLSimplifier


def test_html_simplifier():
    # Given a sample HTML content
    html_content = """
    <html>
        <head>
            <title>Sample Title</title>
        </head>
        <body>
            <p>This is a sample paragraph with a note [1].</p>
            <p>Another paragraph with a modifier [modifier | modifier le code].</p>
            <div class="unnecessary">This should be removed.</div>
        </body>
    </html>
    """
    simplifier = HTMLSimplifier()

    # When processing the HTML content
    simplified_content = simplifier.process(html_content)

    # Then the simplified content should not contain notes or modifiers
    soup = BeautifulSoup(simplified_content, "html.parser")
    assert soup.find("title").get_text() == "Sample Title"
    assert soup.find("div", class_="unnecessary") is None
    assert "This is a sample paragraph with a note" in simplified_content


def test_html_simplifier_empty():
    # Given an empty HTML content
    html_content = ""
    simplifier = HTMLSimplifier()

    # When processing the empty HTML content
    simplified_content = simplifier.process(html_content)

    # Then the simplified content should also be empty
    assert simplified_content == ""


def test_html_simplifier_no_notes():
    # Given HTML content without notes or modifiers
    html_content = """
    <html>
        <head>
            <title>Sample Title</title>
        </head>
        <body>
            <p>This is a sample paragraph with a note [1].</p>
        </body>
    </html>
    """
    simplifier = HTMLSimplifier()

    # When processing the HTML content
    simplified_content = simplifier.process(html_content)

    # Then the simplified content should remain unchanged except for unnecessary tags
    assert "[1]" not in simplified_content


def test_html_simplifier_with_modifiers():
    # Given HTML content with modifiers
    html_content = """
    <html>
        <head>
            <title>Sample Title</title>
        </head>
        <body>
            <p>ce qui est entre brackets doit être viré [modifier | modifier le code].</p>
        </body>
    </html>
    """
    simplifier = HTMLSimplifier()

    # When processing the HTML content
    simplified_content = simplifier.process(html_content)

    # Then the simplified content should not contain the modifier
    assert "modifier" not in simplified_content
    assert "modifier le code" not in simplified_content
    assert "[" not in simplified_content
    assert "]" not in simplified_content
    assert "|" not in simplified_content

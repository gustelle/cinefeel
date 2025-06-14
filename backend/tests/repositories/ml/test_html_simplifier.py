import pytest
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
            <section>
                <h2>Sample Section</h2>
                <div>
                    <p>This is a sample paragraph with a note [1].</p>
                    <p>Another paragraph with a modifier [modifier | modifier le code].</p>
                    <div class="unnecessary">This should remain.</div>
                </div>
            </section>
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
    assert "This should remain." in simplified_content


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


def test_a_tags_are_removed():
    # Given HTML content with <a> tags
    html_content = """
    <html>
        <head>
            <title>Sample Title</title>
        </head>
        <body>
            <p>This is a sample paragraph with a link <a href="http://example.com">Example</a>.</p>
        </body>
    </html>
    """
    simplifier = HTMLSimplifier()

    # When processing the HTML content
    simplified_content = simplifier.process(html_content)

    # Then the simplified content should not contain <a> tags
    soup = BeautifulSoup(simplified_content, "html.parser")
    assert soup.find("a") is None, "The <a> tag should be removed from the content."


def test_line_breaks_are_replaced_with_newlines():
    # Given HTML content with <br> tags
    html_content = """
    <html>
        <head>
            <title>Sample Title</title>
        </head>
        <body>
            <p>Né le 18 février 1864<br>Paris 10e</p>
        </body>
    </html>
    """
    simplifier = HTMLSimplifier()

    # When processing the HTML content
    simplified_content = simplifier.process(html_content)

    # Then the simplified content should have newlines instead of <br> tags
    assert "\n" in simplified_content
    assert "Né le 18 février 1864\nParis 10e" in simplified_content


def test_html_simplifier_contains_no_minor_tags():
    """
    things like <b>, <i>, <strong>, <em>, <time>, <code>, <pre>, <blockquote>, <a>, <span>, <small>
    are removed from the HTML content.
    """

    # Given a sample HTML content
    html_content = """
    <html>
        <head>
            <title>Sample Title</title>
        </head>
        <body>
            <section>
                <h2>Sample Section</h2>
                <table><caption class="hidden" style="">Données clés</caption>
                <tbody>
                <tr>
                    <th scope="row">Nom de naissance</th>
                    <td>Ferdinand Louis Zecca</td>
                </tr>
                <tr>
                    <th scope="row">Naissance</th>
                    <td>
                    <time class="nowrap date-lien bday" datetime="1864-02-19" data-sort-value="1864-02-19"><a rel="mw:WikiLink" href="./19_février" title="19 février">19</a> <a rel="mw:WikiLink" href="./Février_1864" title="Février 1864">février</a> <a rel="mw:WikiLink" href="./1864" title="1864">1864</a></time><br><a rel="mw:WikiLink" href="./Paris" title="Paris">Paris</a> 10<sup>e</sup></td>
                </tr>
                <tr>
                <th scope="row">Nationalité</th>
                <td>
                    <span class="flagicon" data-sort-value=""><span class="mw-image-border noviewer" typeof="mw:File" data-mw="{&quot;caption&quot;:&quot;Drapeau de la France&quot;}"><a href="./Fichier:Flag_of_France_(lighter_variant).svg" class="mw-file-description" title="Drapeau de la France"><img alt="Drapeau de la France" resource="./Fichier:Flag_of_France_(lighter_variant).svg" src="//upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Flag_of_France_%281976%E2%80%932020%29.svg/20px-Flag_of_France_%281976%E2%80%932020%29.svg.png" decoding="async" data-file-width="900" data-file-height="600" data-file-type="drawing" height="13" width="20" srcset="//upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Flag_of_France_%281976%E2%80%932020%29.svg/40px-Flag_of_France_%281976%E2%80%932020%29.svg.png 1.5x, //upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Flag_of_France_%281976%E2%80%932020%29.svg/40px-Flag_of_France_%281976%E2%80%932020%29.svg.png 2x" class="mw-file-element"></a></span></span> <a rel="mw:WikiLink" href="./France" title="France">Française</a></td>
                </tr>
                <tr>
                    <th scope="row">Small</th>
                    <td><small>text</small></td>
                </tr>
                <tr>
                    <th scope="row">Code</th>
                    <td><code>text</code></td>
                </tr>
                <tr>
                    <th scope="row">pre</th>
                    <td><pre>text</pre></td>
                </tr>
                <tr>
                    <th scope="row">blockquote</th>
                    <td><blockquote>text</blockquote></td>
                </tr>
                <tr>
                    <th scope="row">b, em, strong et i</th>
                    <td><b>text</b>, <em>text</em>, <strong>text</strong> et <i>text</i></td>
                </tr>
                <tr>
                    <th scope="row">sub et sup</th>
                    <td><sub>text</sub> et <sup>text</sup></td>
                </tr>
                
                </tbody></table>
            </section>
        </body>
    </html>
    """
    simplifier = HTMLSimplifier()

    # When processing the HTML content
    simplified_content = simplifier.process(html_content)

    # Then the simplified content should not contain notes or modifiers
    soup = BeautifulSoup(simplified_content, "html.parser")

    assert (
        soup.find("time") is None
    ), "The <time> tag should be removed from the content."
    assert (
        soup.find("code") is None
    ), "The <code> tag should be removed from the content."
    assert soup.find("pre") is None, "The <pre> tag should be removed from the content."
    assert (
        soup.find("blockquote") is None
    ), "The <blockquote> tag should be removed from the content."
    assert soup.find("a") is None, "The <a> tag should be removed from the content."
    assert (
        soup.find("span") is None
    ), "The <span> tag should be removed from the content."
    assert (
        soup.find("small") is None
    ), "The <small> tag should be removed from the content."
    assert soup.find("b") is None, "The <b> tag should be removed from the content."
    assert soup.find("i") is None, "The <i> tag should be removed from the content."
    assert (
        soup.find("strong") is None
    ), "The <strong> tag should be removed from the content."
    assert soup.find("em") is None, "The <em> tag should be removed from the content."
    assert soup.find("sup") is None, "The <sup> tag should be removed from the content."
    assert soup.find("sub") is None, "The <sub> tag should be removed from the content."


@pytest.mark.skip(reason="Infobox preservation is not implemented yet.")
def test_infobox_is_preserved(read_melies_html):
    # Given HTML content with an infobox

    simplifier = HTMLSimplifier()

    # When processing the HTML content
    simplified_content = simplifier.process(read_melies_html)

    # Then the infobox should be preserved
    soup = BeautifulSoup(simplified_content, "html.parser")

    print(soup.prettify())

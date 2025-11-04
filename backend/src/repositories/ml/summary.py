import nltk
import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from src.exceptions import SummaryError
from src.interfaces.content_splitter import Section
from src.interfaces.nlp_processor import Processor
from src.settings import MLSettings

from .cache import load_transformer
from .lexrank import degree_centrality_scores


class SectionSummarizer(Processor[Section]):
    """
    summarize the content of a section.
    """

    _summarizer: SentenceTransformer
    _settings: MLSettings

    def __init__(
        self,
        settings: MLSettings,
    ) -> None:

        self._settings = settings

        self._summarizer = load_transformer(
            model=settings.summary_model, backend=settings.transformer_model_backend
        )

        logger.info(
            f"SectionSummarizer initialized with backend '{self._summarizer.backend}' on device: {self._summarizer.device}",
        )

    def process(self, section: Section) -> Section | None:
        """
        Process a section to summarize its content if it exceeds the maximum length.

        The title of the section is preserved, and the content is summarized using a BERT model

        Children sections are processed as well recursively.

        Example:
        ```python
        section = Section(title="Example Section", content="This is a long content that needs summarization.")
        summarizer = SectionSummarizer(settings)
        summarized_section = summarizer.process(section)
        ```

        Args:
            section (Section): The section to process.

        Returns:
            Section: A new section with summarized content if the original content is too long,
                     otherwise the original section.
            None: If the section is None or empty.
        """
        return self._process_section(section)

    def _process_section(self, section: Section) -> Section:
        """
        Processes a single section to summarize its content.

        Args:
            section (Section): The section to process.

        Returns:
            Section: The processed section with summarized content.
        """

        try:

            new_content = section.content
            title = section.title

            if len(section.content) > self._settings.summary_max_length:

                sentences = nltk.sent_tokenize(section.content, language="french")

                # Compute the sentence embeddings
                embeddings = self._summarizer.encode(sentences)

                # Compute the similarity scores
                similarity_scores = self._summarizer.similarity(
                    embeddings, embeddings
                ).numpy()

                # Compute the centrality for each sentence
                centrality_scores = degree_centrality_scores(
                    similarity_scores, threshold=None
                )

                # We argsort so that the first element is the sentence with the highest score
                most_central_sentence_indices = np.argsort(-centrality_scores)
                num_sentences_to_keep = len(sentences) // 3
                new_content = " ".join(
                    [
                        sentences[idx]
                        for idx in most_central_sentence_indices[:num_sentences_to_keep]
                    ]
                )
                logger.info(
                    f"Section '{title}' content summarized from {len(section.content)} to {len(new_content)} characters."
                )

            children = None
            if section.children:
                children = []
                for child in section.children:
                    children.append(
                        Section(
                            title=child.title,
                            content=child.content,
                            children=[
                                self._process_section(grandchild)
                                for grandchild in child.children
                            ],
                            media=child.media,
                        )
                    )

            return Section(
                title=title, content=new_content, children=children, media=section.media
            )

        except Exception as e:

            raise SummaryError(f"Error summarizing content: {e}") from e

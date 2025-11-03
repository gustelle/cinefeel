from functools import cache

import nltk
import torch
from loguru import logger
from sentence_transformers import SentenceTransformer

# load once
nltk.download("punkt_tab")


@cache
def load_transformer(model: str, backend: str) -> SentenceTransformer:
    """cache the embedder instance to avoid re-loading the model multiple times
    which causes 429 errors when calling HuggingFace API too often
    """
    logger.info(f"Loading transformer model '{model}' with backend '{backend}'")

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available() else "cpu"
    )
    return SentenceTransformer(
        model,
        backend=backend,
        device=device,
    )

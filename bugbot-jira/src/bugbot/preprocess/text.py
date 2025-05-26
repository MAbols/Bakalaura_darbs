# src/bugbot/preprocess/text.py
from __future__ import annotations

import re
import unicodedata
from typing import Iterable

import emoji
import nltk
from nltk import sent_tokenize, download

def _ensure_nltk_resource(resource_id: str, download_pkg: str) -> None:
    try:
        nltk.data.find(resource_id)
    except LookupError:
        nltk.download(download_pkg, quiet=True)

_ensure_nltk_resource("tokenizers/punkt", "punkt")
_ensure_nltk_resource("corpora/stopwords", "stopwords")

# first-time download guard (small, cached in ~/.cache/nltk/)
download("punkt_tab", quiet=True)
download("stopwords", quiet=True)

_STOPWORDS = set(word.lower() for word in
                 ("the", "and", "to", "a", "of", "in"))  #  quick stub


def _normalise_unicode(text: str) -> str:
    """NFKC normalisation + emoji demojise + strip accents."""
    text = unicodedata.normalize("NFKC", text)
    text = emoji.demojize(text, delimiters=(":", ":"))
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return text


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_freeform(raw: str, *, drop_stopwords: bool = False) -> str:
    """
    Canonicalise a tester’s free-form bug note.

    Steps:
    1. Unicode/emoji normalisation (Denny & Spirling 2018 show
       preprocessing greatly improves downstream NLP accuracy).
    2. Lower-casing.
    3. Optional stop-word pruning.
    4. Whitespace collapse.
    """
    text = _normalise_unicode(raw).lower()
    if drop_stopwords:
        words = [w for w in text.split() if w not in _STOPWORDS]
        text = " ".join(words)
    return _collapse_whitespace(text)


def split_sentences(text: str) -> list[str]:
    """Sentence tokeniser wrapper (language-agnostic)."""
    return [s.strip() for s in sent_tokenize(text) if s.strip()]

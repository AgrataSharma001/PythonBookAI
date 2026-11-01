import json
import re

import numpy as np

from config import INDEX_DIR
from embeddings import embed_texts, embed_query


EMBEDDINGS_FILE = INDEX_DIR / "embeddings.npy"
METADATA_FILE = INDEX_DIR / "metadata.json"


# ---------------------------------------------------------
# CREATE INDEX
# ---------------------------------------------------------
def save_index(chunks: list[dict]):

    if not chunks:
        print("No chunks to save.")
        return

    # Identify PDFs being indexed
    new_sources = {
        chunk["source"] for chunk in chunks
    }

    texts = [chunk["text"] for chunk in chunks]

    print("Creating embeddings...")

    new_embeddings = embed_texts(texts)

    # Check existing index files
    embeddings_exist = EMBEDDINGS_FILE.exists()
    metadata_exist = METADATA_FILE.exists()

    if embeddings_exist != metadata_exist:
        raise RuntimeError(
            "Index files are incomplete. Check the existing index."
        )

    if embeddings_exist and metadata_exist:

        old_embeddings = np.load(EMBEDDINGS_FILE)

        with open(METADATA_FILE, "r", encoding="utf-8") as file:
            old_metadata = json.load(file)

        if len(old_embeddings) != len(old_metadata):
            raise RuntimeError(
                "Embedding and metadata counts do not match."
            )

        # Keep PDFs that are not being re-indexed
        keep_indices = [
            index
            for index, item in enumerate(old_metadata)
            if item["source"] not in new_sources
        ]

        old_embeddings = old_embeddings[keep_indices]

        old_metadata = [
            old_metadata[index]
            for index in keep_indices
        ]

        # Combine old and new data
        embeddings = np.vstack([
            old_embeddings,
            new_embeddings
        ])

        metadata = old_metadata + chunks

    else:

        embeddings = new_embeddings
        metadata = chunks

    # Assign unique IDs
    for index, chunk in enumerate(metadata):
        chunk["id"] = index

    # Save embeddings
    np.save(EMBEDDINGS_FILE, embeddings)

    # Save metadata
    with open(METADATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\nIndex updated successfully!")
    print("Total indexed chunks:", len(metadata))
    print("Embedding shape:", embeddings.shape)
    print("Updated PDFs:", ", ".join(sorted(new_sources)))

# ---------------------------------------------------------
# LOAD INDEX
# ---------------------------------------------------------

def load_index():

    embeddings = np.load(EMBEDDINGS_FILE)

    with open(METADATA_FILE, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    return embeddings, metadata


# ---------------------------------------------------------
# TOKENIZATION
def tokenize(text: str) -> set[str]:
    """Tokenize text and remove common words that add little search value."""

    stop_words = {
        "a", "an", "the",
        "is", "are", "was", "were",
        "what", "which", "who", "whom",
        "how", "when", "where", "why",
        "do", "does", "did",
        "can", "could", "would", "should",
        "i", "you", "we", "they", "he", "she", "it",
        "me", "my", "your", "our", "their",
        "in", "on", "at", "to", "of", "for",
        "and", "or", "but", "with", "from",
        "about", "explain", "describe", "tell",
        "please", "give", "show"
    }

    words = re.findall(
        r"[A-Za-z_][A-Za-z0-9_]*",
        text.lower()
    )

    normalized = set()

    for word in words:
        if word in stop_words:
            continue

        # Normalize simple plurals.
        if word.endswith("s") and len(word) > 3:
            word = word[:-1]

        normalized.add(word)

    return normalized
# ---------------------------------------------------------
# KEYWORD SCORE
# ---------------------------------------------------------

def keyword_score(query: str, text: str) -> float:

    query_words = tokenize(query)
    text_words = tokenize(text)

    if not query_words:
        return 0.0

    matches = query_words.intersection(text_words)

    return len(matches) / len(query_words)


# ---------------------------------------------------------
# DUPLICATE CHECK
# ---------------------------------------------------------

def is_duplicate(result: dict, selected: list[dict]) -> bool:

    for existing in selected:

        # Same book + same page
        if (
            result["source"] == existing["source"]
            and result["page"] == existing["page"]
        ):
            return True

    return False
# ---------------------------------------------------------
# HYBRID SEARCH
# ---------------------------------------------------------

def search(query: str, top_k=5, source: str | None = None):

    embeddings, metadata = load_index()

    # ---------------------------------------------
    # 1. Semantic search
    # ---------------------------------------------

    query_embedding = embed_query(query)

    semantic_scores = embeddings @ query_embedding

    # ---------------------------------------------
    # 2. Calculate hybrid scores
    # ---------------------------------------------

    candidates = []

    for index, item in enumerate(metadata):
        if source is not None and item.get("source") != source:
            continue
        semantic_score = float(
            semantic_scores[index]
        )

        keyword = keyword_score(
            query,
            item["text"]
        )

        # Weighted combination
        #
        # Semantic = 85%
        # Keyword  = 15%

        hybrid_score = (
            0.85 * semantic_score
            +
            0.15 * keyword
        )

        result = dict(item)

        result["semantic_score"] = semantic_score
        result["keyword_score"] = keyword
        result["score"] = hybrid_score

        candidates.append(result)

    # ---------------------------------------------
    # 3. Sort by hybrid score
    # ---------------------------------------------

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # ---------------------------------------------
    # 4. Remove duplicate chunks
    # ---------------------------------------------

    results = []

    for candidate in candidates:

        if is_duplicate(
            candidate,
            results
        ):
            continue

        results.append(candidate)

        if len(results) >= top_k:
            break

    return results
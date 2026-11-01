from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

BOOKS_DIR = BASE_DIR / "data" / "books"
INDEX_DIR = BASE_DIR / "data" / "index"

# Create folders automatically if they don't exist
BOOKS_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# EMBEDDING MODEL
# ============================================================

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ============================================================
# OLLAMA
# ============================================================

OLLAMA_BASE_URL = "http://127.0.0.1:11434"

OLLAMA_MODEL = "llama3.2:3b"


# ============================================================
# RAG SETTINGS
# ============================================================

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150

TOP_K = 8


# ============================================================
# SUMMARIZATION SETTINGS
# ============================================================

SUMMARY_CHUNK_SIZE = 1800
SUMMARY_CHUNK_OVERLAP    = 200
SUMMARY_BATCH_SIZE = 6
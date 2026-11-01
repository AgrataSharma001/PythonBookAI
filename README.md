# PythonBookAI

PythonBookAI is a local PDF question-answering and summarization
application. It combines PDF text extraction, semantic retrieval,
reranking, and a locally hosted language model.

## Features

-   Upload PDF files and extract text with PyMuPDF.
-   Split text into overlapping chunks.
-   Create 384-dimensional embeddings with
    `sentence-transformers/all-MiniLM-L6-v2`.
-   Store embeddings and metadata in a local index.
-   Retrieve passages using semantic similarity and keyword overlap.
-   Rerank retrieved passages with
    `cross-encoder/ms-marco-MiniLM-L-6-v2`.
-   Generate answers with Ollama (`llama3.2:3b`).
-   Filter questions by a selected PDF.
-   Store conversation history in SQLite.
-   Summarize PDFs using a Map-Reduce pipeline.
-   Display summaries in the browser using Markdown formatting.

## Architecture

### Question answering (RAG)

1.  A PDF is uploaded.
2.  PyMuPDF extracts and cleans page text.
3.  Text is split into overlapping chunks.
4.  Sentence Transformers converts chunks into embeddings.
5.  Embeddings and metadata are stored locally.
6.  A question is embedded and matched against indexed chunks.
7.  Hybrid retrieval combines semantic similarity and keyword overlap.
8.  A cross-encoder reranks the retrieved passages.
9.  Ollama generates an answer grounded in the retrieved context.
10. The answer and source information are returned to the interface.

### Summarization

1.  Extract text from the selected PDF.
2.  Split the text into larger summary chunks.
3.  Summarize batches of chunks (Map stage).
4.  Combine and reduce intermediate summaries.
5.  Generate a final structured summary.

Generated answers and summaries can contain errors or omissions. Verify
important information against the original PDF.

## Technology stack

  Component              Technology
  ---------------------- ------------------------------------------
  Backend                Python, Flask
  Frontend               HTML, CSS, JavaScript
  PDF extraction         PyMuPDF
  Embeddings             Sentence Transformers
  Embedding model        `sentence-transformers/all-MiniLM-L6-v2`
  Reranker               Cross-Encoder
  Reranker model         `cross-encoder/ms-marco-MiniLM-L-6-v2`
  Local LLM runtime      Ollama
  LLM                    `llama3.2:3b`
  Index storage          NumPy `.npy` and JSON metadata
  Conversation storage   SQLite

## Requirements

-   Python.
-   Ollama installed and running.
-   The configured Ollama model downloaded locally.
-   Project dependencies installed in the virtual environment.
-   Internet access may be needed on first use to download embedding and
    reranking models.

## Setup on Windows

Open PowerShell in the project directory.

### 1. Create and activate the virtual environment

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

If the project contains `requirements.txt`:

``` powershell
python -m pip install -r requirements.txt
```

If it does not, install the project's required packages (including
Flask, PyMuPDF, NumPy, Requests, Sentence Transformers, and PyTorch) in
the activated environment. Keep package versions compatible; do not
blindly upgrade NumPy or PyTorch in a working environment.

### 3. Install and prepare Ollama

``` powershell
ollama pull llama3.2:3b
ollama list
```

Make sure the model name and Ollama URL in `config.py` match your local
setup.

### 4. Review configuration

Current project settings include:

-   PDFs: `data/books/`
-   Index: `data/index/`
-   Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
-   Ollama URL: `http://127.0.0.1:11434`
-   Ollama model: `llama3.2:3b`
-   RAG chunk size: 900 characters
-   RAG chunk overlap: 150 characters
-   Summary chunk size: 1800 characters
-   Summary chunk overlap: 200 characters
-   Summary batch size: 6

### 5. Add PDFs and build the index

Place PDFs in `data/books/`, or upload them through the web interface.

If you copied PDFs directly into `data/books/`, run the ingestion
script:

``` powershell
python ingest.py
```

The ingestion script reprocesses PDFs in that directory and can take
time. Do not run it unnecessarily.

### 6. Start the application

``` powershell
python app.py
```

Open `http://127.0.0.1:5000/` in your browser. Stop the server with
`Ctrl+C`.

## Typical workflow

1.  Start Ollama.
2.  Activate `.venv`.
3.  Run `python app.py`.
4.  Open the local application.
5.  Upload a text-based PDF or select an existing one.
6.  Select a specific PDF for document-filtered questions or
    summarization.
7.  Ask a question and inspect the returned source pages.
8.  Use **Summarize PDF** to generate a structured summary.

Large PDFs may take several minutes or longer to summarize on a CPU.
Check the Flask terminal for progress and errors.

## API endpoints

  -----------------------------------------------------------------------
  Endpoint                Method                  Purpose
  ----------------------- ----------------------- -----------------------
  `/`                     GET                     Serves the web
                                                  interface

  `/books`                GET                     Lists available PDF
                                                  files

  `/upload`               POST                    Uploads and indexes a
                                                  PDF

  `/ask`                  POST                    Answers a question
                                                  using retrieved PDF
                                                  context

  `/summarize`            POST                    Summarizes a selected
                                                  PDF

  `/conversations`        GET                     Lists conversations

  `/conversations`        POST                    Creates a conversation

  `/conversations/<id>`   GET                     Retrieves a
                                                  conversation and its
                                                  messages

  `/conversations/<id>`   DELETE                  Deletes a conversation
  -----------------------------------------------------------------------

Example `/summarize` JSON body:

``` json
{
  "filename": "pythonbook1.pdf"
}
```

Example `/ask` JSON body:

``` json
{
  "question": "What is a variable in Python?",
  "source": "pythonbook1.pdf",
  "conversation_id": 1
}
```

The exact optional fields should match the frontend request and current
Flask route implementation.

## Project structure

This is the logical structure based on the current implementation. Check
actual filenames in your working folder before treating it as an exact
directory listing.

``` text
PythonBookAI/
├── app.py
├── config.py
├── pdf_processor.py
├── embeddings.py
├── vector_store.py
├── ingest.py
├── rag.py
├── ollama_client.py
├── summarizer.py
├── templates/
│   └── index.html
├── static/
│   ├── app.js
│   └── style.css
├── data/
│   ├── books/
│   └── index/
└── .venv/
```

## Limitations

-   Scanned/image-only PDFs may not work because OCR is not implemented.
-   Local CPU summarization can be slow for large PDFs.
-   Summaries and answers may omit details or generate inaccurate
    claims. Check important claims against the source.
-   Long synchronous requests can make the development interface appear
    unresponsive.
-   Keep the embedding file and metadata file together; do not edit one
    index file independently.
-   The Flask development server is not a production deployment.
-   A Hugging Face token is optional for ordinary model downloads, but
    authentication may help with rate limits.

## Troubleshooting

### Python package import error

Check that the virtual environment is active:

``` powershell
python -c "import sys; print(sys.executable)"
```

The path should point inside the project's `.venv` folder.

### Ollama connection error

Confirm Ollama is running and check the installed model:

``` powershell
ollama list
```

### No extractable text

The PDF may be scanned or image-only. OCR is not currently implemented.

### Index mismatch

If an index-check script is present, run it. The number of embedding
rows must equal the number of metadata records, and the embedding
dimension should be 384 for the configured embedding model.

## Development status

The core workflow has been exercised: PDF upload and indexing,
source-filtered retrieval and question answering, conversation history,
and browser-based PDF summarization. Complete the final regression
checklist before presenting or submitting the project.

## License and attribution

Add the license and attribution terms that apply to your own code and to
third-party libraries, models, datasets, and source PDFs.

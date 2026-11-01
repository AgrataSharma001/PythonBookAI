# PythonBookAI --- Final End-to-End Test Checklist

Run tests from the project directory with `.venv` activated. Keep the
Flask terminal visible so backend errors and progress messages are not
missed.

## 1. Environment and startup

-   [ ] Activate the environment:

    ``` powershell
    .\.venv\Scripts\Activate.ps1
    ```

-   [ ] Verify Python:

    ``` powershell
    python -c "import sys; print(sys.executable)"
    ```

    Expected: Python executable is inside the project's `.venv`.

-   [ ] Verify key imports:

    ``` powershell
    python -c "import flask, pymupdf, numpy, requests, sentence_transformers, torch; print('Imports OK')"
    ```

-   [ ] Confirm Ollama and the configured model:

    ``` powershell
    ollama list
    ```

-   [ ] Compile the Flask app:

    ``` powershell
    python -m py_compile app.py
    ```

    Expected: no syntax errors.

-   [ ] Start the app using `python app.py`.

-   [ ] Open `http://127.0.0.1:5000/`. Expected: interface loads without
    a server traceback.

## 2. PDF upload and indexing

Use a small, text-based PDF first.

-   [ ] Upload a valid PDF. Expected: success message with filename,
    pages, and chunks.
-   [ ] Confirm the PDF appears in the book selector.
-   [ ] Upload the same filename again. Expected: duplicate-file
    response (HTTP 409).
-   [ ] Try a non-PDF renamed with a `.pdf` extension. Expected:
    validation rejects it.
-   [ ] Try a scanned PDF if available. Expected with current
    implementation: no-extractable-text response; OCR is not
    implemented.
-   [ ] Run the index-check script if present. Expected: embedding count
    equals metadata count; embedding dimension is 384.

## 3. Retrieval and question answering

-   [ ] Select one known PDF.
-   [ ] Ask a question whose answer is explicitly stated in that PDF.
-   [ ] Compare the generated answer with the original document.
-   [ ] Verify source filename and page numbers.
-   [ ] Ask something not answered in the selected PDF. Check that the
    system does not confidently invent a source-backed answer.
-   [ ] Select **All Books** and ask a question answered in a different
    indexed PDF. Confirm the retrieval scope changes.
-   [ ] Ask a follow-up question in the same conversation.

## 4. Conversation history

-   [ ] Create a new conversation.
-   [ ] Send a question and receive an answer.
-   [ ] Refresh the browser. Expected: conversation remains listed.
-   [ ] Reopen it. Expected: previous messages appear.
-   [ ] Delete a test conversation. Expected: it disappears and cannot
    be reopened.

## 5. PDF summarization

Start with a short PDF.

-   [ ] Select a specific PDF, not **All Books**.
-   [ ] Click **Summarize PDF**.
-   [ ] Confirm progress status appears and the button is disabled
    during processing.
-   [ ] Watch the Flask terminal for extraction, chunking, batch
    summaries, reduction, and final summary.
-   [ ] Confirm the summary appears with headings, paragraphs, and
    lists.
-   [ ] Compare at least five factual statements with the original PDF.
-   [ ] Check for repeated points, missing spaces, unsupported claims,
    and major omissions.
-   [ ] Try summarizing with **All Books** selected. Expected: prompt to
    select a specific PDF.
-   [ ] Test a large PDF only after the short-PDF test passes. Record
    duration and check for server errors or `Failed to fetch`.

## 6. Frontend and error handling

-   [ ] Refresh the page and confirm the book dropdown loads existing
    PDFs.
-   [ ] Confirm upload and summary status messages are understandable.
-   [ ] Check the browser developer console for uncaught JavaScript
    errors.
-   [ ] Check the Flask terminal for tracebacks.
-   [ ] Submit an empty question and confirm clean validation.
-   [ ] Confirm failed requests do not leave buttons permanently
    disabled.
-   [ ] Confirm chat still works after a summary is displayed.

## 7. Demo acceptance criteria

Do not call the project demo-ready until these critical checks pass:

1.  App starts using the documented environment.
2.  A valid PDF uploads and is indexed.
3.  A question retrieves relevant text from the selected PDF.
4.  The answer's source filename and page are verifiable.
5.  Conversation history survives a browser refresh.
6.  A short PDF summary completes and displays correctly.
7.  The summary is checked against the original document.
8.  No unresolved backend traceback or frontend failure occurs in the
    demo workflow.

## Test record

  Test                                 Pass/Fail   Notes or evidence
  ------------------------------------ ----------- -------------------
  Environment and startup                          
  PDF upload and indexing                          
  Duplicate upload validation                      
  Source-filtered question answering               
  All-books retrieval                              
  Conversation persistence                         
  Conversation deletion                            
  Short PDF summarization                          
  Summary factual review                           
  Large PDF behavior                               
  Frontend/browser console                         

**Important:** A button responding or a fluent model answer is not proof
of correctness. Verify stored index consistency, retrieved source pages,
and generated content.

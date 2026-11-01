from pathlib import Path

from ollama_client import generate
from pdf_processor import extract_pages
from config import (
    SUMMARY_CHUNK_SIZE,
    SUMMARY_CHUNK_OVERLAP,
    SUMMARY_BATCH_SIZE
)


# ==========================================
# 1. SPLIT DOCUMENT INTO SMALLER CHUNKS
# ==========================================

def split_text_into_chunks(text):
    """
    Divide document text into overlapping chunks.
    """

    chunks = []

    chunk_size = SUMMARY_CHUNK_SIZE
    overlap = SUMMARY_CHUNK_OVERLAP

    if chunk_size <= 0:
        raise ValueError("SUMMARY_CHUNK_SIZE must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "SUMMARY_CHUNK_OVERLAP must be non-negative "
            "and smaller than SUMMARY_CHUNK_SIZE."
        )

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# ==========================================
# 2. SUMMARIZE A SINGLE BATCH
# ==========================================

def summarize_batch(chunks, batch_number):
    """
    Generate a summary from a group of text chunks.
    """

    combined_text = "\n\n".join(chunks)

    prompt = f"""
You are an expert document summarization assistant.

Summarize the following document sections.

Instructions:

1. Identify the main topics.
2. Extract important facts and concepts.
3. Preserve important technical details.
4. Remove unnecessary repetition.
5. Do not invent information.
6. Use simple, clear language.
7. Do not introduce outside knowledge.

DOCUMENT SECTIONS:

{combined_text}

Write a structured summary with:
- Main topics
- Important points
- Technical details
- Key findings
"""

    print(f"Summarizing batch {batch_number}...")

    return generate(prompt, temperature=0.2)


# ==========================================
# 3. REDUCE MULTIPLE SUMMARIES
# ==========================================

def reduce_summaries(summaries):
    """
    Combine multiple summaries into a smaller set.
    Repeatedly reduces them until they fit into
    one final summarization request.
    """

    batch_size = SUMMARY_BATCH_SIZE

    if batch_size < 2:
        raise ValueError("SUMMARY_BATCH_SIZE must be at least 2.")

    level = 1

    while len(summaries) > batch_size:

        print(f"\nReducing summary level {level}...")

        new_summaries = []

        for i in range(0, len(summaries), batch_size):

            batch = summaries[i:i + batch_size]

            prompt = f"""
You are an expert summarization assistant.

Combine the following summaries into one concise summary.

Instructions:
- Preserve all important information.
- Remove repeated information.
- Preserve important technical details.
- Do not invent facts.
- Use only the provided information.

SUMMARIES:

{chr(10).join(batch)}

Create a clear, structured summary.
"""

            result = generate(prompt, temperature=0.2)

            new_summaries.append(result)

        summaries = new_summaries
        level += 1

    return summaries


# ==========================================
# 4. GENERATE FINAL SUMMARY
# ==========================================

def generate_final_summary(summaries):
    """
    Generate the final structured document summary.
    """

    combined_summaries = "\n\n".join(summaries)

    prompt = f"""
You are an expert document summarization assistant.

Prepare a comprehensive summary of the original document
using the intermediate summaries below.

Use exactly these four sections:

1. EXECUTIVE SUMMARY

Explain the overall purpose and content of the document.

2. KEY POINTS

List the most important concepts, facts and findings
in bullet points.

3. DETAILED SUMMARY

Explain the major topics and their relationships.
Preserve important technical details.

4. CONCLUSION

Explain the main takeaway of the document.

IMPORTANT RULES:

- Use only information supported by the summaries.
- Do not invent facts or examples.
- Avoid unnecessary repetition.
- Use clear and understandable language.
- Preserve important technical terminology.
- If information is unavailable, do not guess.

INTERMEDIATE SUMMARIES:

{combined_summaries}
"""

    print("\nGenerating final summary...")

    return generate(prompt, temperature=0.2)


# ==========================================
# 5. MAIN PDF SUMMARIZATION FUNCTION
# ==========================================

def summarize_pdf(pdf_path):
    """
    Complete PDF summarization pipeline.

    Steps:
    1. Extract PDF text.
    2. Split text into chunks.
    3. Summarize chunks in batches.
    4. Reduce intermediate summaries.
    5. Generate final summary.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    print("\n================================")
    print("STARTING PDF SUMMARIZATION")
    print("================================")

    # Step 1: Extract PDF text
    print("\nExtracting PDF text...")

    pages = extract_pages(pdf_path)

    if not pages:
        raise ValueError(
            "No extractable text found in this PDF. "
            "It may be scanned or image-based."
        )

    print(f"Pages extracted: {len(pages)}")

    # Step 2: Combine page text
    full_text = "\n\n".join(
        f"Page {page['page']}:\n{page['text']}"
        for page in pages
    )

    # Step 3: Split document into chunks
    print("\nSplitting document into chunks...")

    chunks = split_text_into_chunks(full_text)

    if not chunks:
        raise ValueError("Could not create text chunks.")

    print(f"Total chunks: {len(chunks)}")

    # Step 4: Summarize chunks in batches
    print("\nGenerating intermediate summaries...")

    intermediate_summaries = []

    batch_size = SUMMARY_BATCH_SIZE

    for i in range(0, len(chunks), batch_size):

        batch = chunks[i:i + batch_size]

        batch_number = (i // batch_size) + 1

        summary = summarize_batch(
            batch,
            batch_number
        )

        intermediate_summaries.append(summary)

    # Step 5: Reduce intermediate summaries
    print("\nCombining intermediate summaries...")

    reduced_summaries = reduce_summaries(
        intermediate_summaries
    )

    # Step 6: Generate final summary
    final_summary = generate_final_summary(
        reduced_summaries
    )

    print("\n================================")
    print("SUMMARIZATION COMPLETED")
    print("================================")

    return {
        "filename": pdf_path.name,
        "total_pages": len(pages),
        "total_chunks": len(chunks),
        "summary": final_summary
    }
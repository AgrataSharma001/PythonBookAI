from pathlib import Path
from summarizer import summarize_pdf

pdf_path = Path("data/books/EJ1172284.pdf")

try:
    result = summarize_pdf(pdf_path)

    print("\n========== FINAL RESULT ==========")

    print("Filename:", result["filename"])
    print("Pages:", result["total_pages"])
    print("Chunks:", result["total_chunks"])

    print("\nSUMMARY:\n")
    print(result["summary"])

except Exception as error:
    print("ERROR:", error)
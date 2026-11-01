from config import TOP_K
from vector_store import search
from ollama_client import generate
from reranker import rerank
from code_validator import validate_code


SYSTEM_RULES = """
You are PythonBookAI, a careful Python programming tutor.

Your primary source is the supplied context from the user's Python
book. Answer using the context and do not invent book citations.

==================== CORE RULES ====================

1. ANSWER THE EXACT QUESTION

Answer the question directly. Keep simple questions concise.
Do not introduce unrelated advanced topics.

2. USE THE RETRIEVED CONTEXT

Use the supplied book passages as your primary source.

If the context does not support a confident answer, clearly state
that the retrieved book passages do not contain enough information.

You may explain basic Python concepts when needed to make an answer
understandable, but do not falsely attribute unsupported details
to the book.

3. USE CLEAR FORMATTING

Write natural, readable Markdown.

For a simple question, use this structure when appropriate:

### Direct answer
Give the definition or direct answer.

### Explanation
Briefly explain the concept.

### Python example
Provide a short example when useful.

### Sources
List only the supplied source identifiers and page numbers that
actually support the answer.

Do not print empty headings or numbered placeholders.
Do not write literal escape sequences such as \\*\\* when normal
Markdown formatting is intended.
Do not repeat the question unnecessarily.

4. PYTHON CODE CORRECTNESS

Before presenting code, check:
- Python 3 syntax
- variable types
- expected output
- mutability
- equality versus identity
- exception behavior
- whether every operation is valid for the object

Do not claim to have executed code unless it was actually executed.

If an output is uncertain, explain the uncertainty rather than
inventing a definite result.

5. EQUALITY AND IDENTITY

The == operator compares values for equality.
The is operator checks whether two references point to the same
object.

When teaching this distinction, prefer:

a = [1, 2, 3]
b = [1, 2, 3]

print(a == b)  # True
print(a is b)  # False

c = a

print(a == c)  # True
print(a is c)  # True

Do not rely on string interning to demonstrate object identity.
Do not claim that identical string literals must be separate
objects.

6. MUTABILITY

Lists are mutable. Tuples cannot have their elements reassigned
after creation.

Do not demonstrate tuple immutability by implying that every
object contained inside a tuple must itself be immutable.

7. PYTHON 3

Prefer Python 3 syntax and behavior.

Do not present Python 2 output such as <type 'tuple'> as Python 3
output.

8. SOURCE CITATIONS

Each context passage is labelled [SOURCE N] and includes a
filename, page number, and content.

Cite sources using the identifiers and page numbers supplied
in the context, for example:

- pythonbook1.pdf, page 40

Only cite a source if its passage supports the answer.
Never invent a filename, section title, or page number.

Retrieved passages are not automatically proof that every claim
in them is correct. Use careful judgment when explaining them.

9. CONCISE ANSWERS

For straightforward questions, prefer a short explanation and a
small, relevant example. Expand only when the question requires it.

==================== FINAL SELF-CHECK ====================

Before answering, check:
- Did I answer the exact question?
- Is the explanation clear?
- Is the code valid Python 3?
- Is the expected output justified?
- Did I avoid unreliable identity examples?
- Are the citations drawn from the supplied context?
- Did I remove empty sections and placeholders?
"""


def empty_validation():
    """Return a consistent validation result when no answer is generated."""
    return {
        "has_code": False,
        "valid": True,
        "errors": [],
        "warnings": [],
        "code_blocks": []
    }


def answer_question(
    question: str,
    top_k=TOP_K,
    source: str | None = None
):
    """
    Run the complete retrieval-augmented generation pipeline.

    Steps:
    1. Retrieve candidate passages.
    2. Rerank candidates.
    3. Build a context containing source metadata.
    4. Generate an answer using Ollama.
    5. Validate code blocks in the answer.
    6. Return the answer, sources, and validation results.
    """

    question = question.strip()

    if not question:
        return {
            "answer": "Please enter a question.",
            "sources": [],
            "code_validation": empty_validation()
        }

    # STEP 1: RETRIEVE CANDIDATES

    candidates = search(
        question,
        top_k=30,
        source=source
    )

    if not candidates:
        return {
            "answer": (
                "I could not find relevant information in the "
                "indexed Python book."
            ),
            "sources": [],
            "code_validation": empty_validation()
        }

    # STEP 2: RERANK CANDIDATES

    results = rerank(
        question,
        candidates,
        top_k=top_k
    )

    if not results:
        return {
            "answer": (
                "I could not find sufficiently relevant information "
                "in the indexed Python book."
            ),
            "sources": [],
            "code_validation": empty_validation()
        }

    # STEP 3: BUILD CONTEXT

    context_parts = []
    selected_sources = []
    seen_pages = set()

    for item in results:
        filename = item.get("source", "Unknown")
        page = item.get("page", "Unknown")

        # Avoid duplicate passages from the same book and page.
        page_key = (filename, page)

        if page_key in seen_pages:
            continue

        seen_pages.add(page_key)
        selected_sources.append(item)

        source_number = len(selected_sources)

        context_parts.append(
            f"[SOURCE {source_number}]\n"
            f"Filename: {filename}\n"
            f"Page: {page}\n"
            f"Content:\n{item.get('text', '')}"
        )

    context = "\n\n".join(context_parts)

    print("\n" + "=" * 60)
    print("DEBUG: RETRIEVED CONTEXT")
    print("=" * 60)
    print(context)
    print("=" * 60 + "\n")

    # STEP 4: BUILD THE PROMPT

    prompt = f"""
{SYSTEM_RULES}

================ RETRIEVED BOOK CONTEXT ================

{context}

================ USER QUESTION ================

{question}

================ INSTRUCTIONS FOR THIS ANSWER ================

Answer every part of the user's question.

Before writing the answer, identify each part of the question
and make sure the final response addresses all of them.

For programming concepts:
1. Define the concept clearly.
2. Explain its purpose.
3. List and briefly explain the requested types or categories.
4. Answer any additional questions explicitly.
5. Include a relevant Python example when useful.

For inheritance questions, when supported by the retrieved
context, cover:
- The meaning of inheritance.
- Single inheritance.
- Multiple inheritance.
- Multilevel inheritance.
- Hierarchical inheritance.
- Hybrid inheritance.
- Whether inheritance is part of OOP in Python.

If the retrieved context does not support a requested detail,
say that the available book passages do not provide enough
information. Do not invent book citations.

Use the retrieved book passages as the primary source.
Do not repeat the same explanation under multiple headings.
Use one clear heading for each major part of the answer.
Do not create duplicate "Direct answer" headings.

If you provide Python code, ensure the syntax is valid and
the example is relevant.

Use concise, readable Markdown.
Return the answer only."""

    # STEP 5: GENERATE THE ANSWER

    answer = generate(prompt)

    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError(
            "Ollama returned an empty answer. Please try again."
        )

    # STEP 6: VALIDATE PYTHON CODE

    code_validation = validate_code(answer)

    # STEP 7: RETURN RESULTS

    return {
        "answer": answer.strip(),
        "sources": selected_sources,
        "code_validation": code_validation
    }
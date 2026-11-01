from vector_store import load_index

try:
    embeddings, metadata = load_index()

    print("\n========== INDEX DETAILS ==========")

    print("Total embeddings:", len(embeddings))
    print("Total metadata:", len(metadata))
    print("Embedding dimensions:", embeddings.shape)

    print("\n========== INDEXED PDF FILES ==========")

    books = sorted(set(
        item["source"] for item in metadata
    ))

    for book in books:
        count = sum(
            1 for item in metadata
            if item["source"] == book
        )

        print(f"{book}: {count} chunks")

    print("\nIndex check completed.")

except Exception as error:
    print("Index check failed:", error)
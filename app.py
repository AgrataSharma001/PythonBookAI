from werkzeug.utils import secure_filename

from config import BOOKS_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from pdf_processor import extract_pages, chunk_pages
from vector_store import save_index
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from rag import answer_question
from summarizer import summarize_pdf
from database import (
    initialize_database,
    create_conversation,
    save_message,
    get_conversations,
    get_messages,
    delete_conversation
)

app = Flask(__name__)
# Maximum PDF upload size: 50 MB
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
# Initialize database
initialize_database()


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# CREATE NEW CONVERSATION
# ==========================================

@app.route("/conversations", methods=["POST"])
def new_conversation():
    try:
        conversation_id = create_conversation()

        return jsonify({
            "conversation_id": conversation_id,
            "message": "Conversation created successfully."
        }), 201

    except Exception:
        app.logger.exception("Conversation creation failed")

        return jsonify({
            "error": "Could not create conversation."
        }), 500


# ==========================================
# GET ALL CONVERSATIONS
# ==========================================

@app.route("/conversations", methods=["GET"])
def list_conversations():
    try:
        conversations = get_conversations()

        return jsonify({
            "conversations": conversations
        })

    except Exception:
        app.logger.exception("Could not retrieve conversations")

        return jsonify({
            "error": "Could not load conversations."
        }), 500


# ==========================================
# GET MESSAGES FROM A CONVERSATION
# ==========================================

@app.route(
    "/conversations/<int:conversation_id>",
    methods=["GET"]
)
def conversation_messages(conversation_id):
    try:
        conversations = get_conversations()

        exists = any(
            item["id"] == conversation_id
            for item in conversations
        )

        if not exists:
            return jsonify({
                "error": "Conversation not found."
            }), 404

        messages = get_messages(conversation_id)

        return jsonify({
            "conversation_id": conversation_id,
            "messages": messages
        })

    except Exception:
        app.logger.exception("Could not retrieve messages")

        return jsonify({
            "error": "Could not load conversation."
        }), 500


# ==========================================
# DELETE CONVERSATION
# ==========================================

@app.route(
    "/conversations/<int:conversation_id>",
    methods=["DELETE"]
)
def remove_conversation(conversation_id):
    try:
        deleted = delete_conversation(conversation_id)

        if not deleted:
            return jsonify({
                "error": "Conversation not found."
            }), 404

        return jsonify({
            "message": "Conversation deleted successfully."
        })

    except Exception:
        app.logger.exception("Conversation deletion failed")

        return jsonify({
            "error": "Could not delete conversation."
        }), 500
# ==========================================
# UPLOAD PDF
# ==========================================

@app.route("/upload", methods=["POST"])
def upload_pdf():

    saved_path = None

    try:
        if "file" not in request.files:
            return jsonify({"error": "No file was selected."}), 400

        file = request.files["file"]

        if not file.filename:
            return jsonify({"error": "Please select a PDF file."}), 400

        filename = secure_filename(file.filename)

        if not filename:
            return jsonify({"error": "Invalid filename."}), 400

        if not filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are allowed."}), 400

        file_signature = file.stream.read(5)
        file.stream.seek(0)

        if file_signature != b"%PDF-":
            return jsonify({"error": "The selected file is not a valid PDF."}), 400

        saved_path = BOOKS_DIR / filename

        if saved_path.exists():
            return jsonify({
                "error": "A PDF with this filename already exists."
            }), 409

        file.save(saved_path)

        pages = extract_pages(saved_path)

        if not pages:
            saved_path.unlink()
            return jsonify({
                "error": "No extractable text found in this PDF."
            }), 400

        chunks = chunk_pages(
            pages,
            chunk_size=CHUNK_SIZE,
            overlap=CHUNK_OVERLAP
        )

        if not chunks:
            saved_path.unlink()
            return jsonify({
                "error": "Could not create text chunks."
            }), 400

        save_index(chunks)

        return jsonify({
            "message": "PDF uploaded and indexed successfully!",
            "filename": filename,
            "pages": len(pages),
            "chunks": len(chunks)
        }), 201

    except Exception:
        app.logger.exception("PDF upload failed")

        if saved_path and saved_path.exists():
            saved_path.unlink()

        return jsonify({
            "error": "PDF processing failed. Check the terminal."
        }), 500


# ========================================
# PDF SUMMARIZATION API
# ========================================

@app.route("/summarize", methods=["POST"])
def summarize():

    data = request.get_json(silent=True) or {}

    filename = data.get("filename", "").strip()

    if not filename:
        return jsonify({
            "error": "Please select a PDF file."
        }), 400

    if Path(filename).name != filename or not filename.lower().endswith(".pdf"):
        return jsonify({
            "error": "Invalid PDF filename."
        }), 400

    pdf_path = BOOKS_DIR / filename

    if not pdf_path.is_file():
        return jsonify({
            "error": "PDF file not found."
        }), 404

    try:
        result = summarize_pdf(pdf_path)

        return jsonify({
            "message": "PDF summarized successfully!",
            "filename": result["filename"],
            "total_pages": result["total_pages"],
            "total_chunks": result["total_chunks"],
            "summary": result["summary"]
        }), 200

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    except Exception:
        app.logger.exception("PDF summarization failed")

        return jsonify({
            "error": "PDF summarization failed. Check the terminal."
        }), 500

# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
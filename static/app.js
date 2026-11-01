// ========================================
// PythonBookAI - Frontend JavaScript
// ========================================

const questionForm = document.getElementById("question-form");
const questionInput = document.getElementById("question-input");
const sendButton = document.getElementById("send-button");
const bookSelect = document.getElementById("book-select");
const chatContainer = document.getElementById("chat-container");
const welcomeScreen = document.getElementById("welcome-screen");
const newChatButton = document.getElementById("new-chat-button");
const conversationList = document.getElementById("conversation-list");
// ========================================
// LOAD PDF BOOKS FROM BACKEND
// ========================================

async function loadBooks() {
    try {
        const response = await fetch("/books");

        if (!response.ok) {
            throw new Error("Could not load books.");
        }

        const data = await response.json();

        data.books.forEach(book => {
            const alreadyExists = Array.from(bookSelect.options)
                .some(option => option.value === book);

            if (!alreadyExists) {
                const option = document.createElement("option");
                option.value = book;
                option.textContent = book;
                bookSelect.appendChild(option);
            }
        });

        console.log("Books loaded:", data.books);

    } catch (error) {
        console.error("Error loading books:", error);
    }
}

// Load books when the application starts
loadBooks();

// Stores the currently active conversation ID.
let currentConversationId = null;
// ========================================
// CONVERSATION MANAGEMENT
// ========================================

// Create a new conversation in the database.
async function createConversation() {
    const response = await fetch("/conversations", {
        method: "POST"
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Could not create conversation.");
    }

    currentConversationId = data.conversation_id;

    await loadConversations();

    return currentConversationId;
}


// ========================================
// LOAD AND DISPLAY CONVERSATION HISTORY
// ========================================

async function loadConversations() {
    try {
        const response = await fetch("/conversations");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Could not load conversations.");
        }

        conversationList.replaceChildren();

        // Show message when there are no saved chats
        if (!data.conversations || data.conversations.length === 0) {
            const emptyMessage = document.createElement("p");
            emptyMessage.className = "empty-history";
            emptyMessage.textContent = "No conversations yet.";
            conversationList.appendChild(emptyMessage);
            return;
        }

        data.conversations.forEach((conversation) => {

            // Main wrapper
            const wrapper = document.createElement("div");
            wrapper.className = "conversation-item-wrapper";

            // Conversation title button
            const chatButton = document.createElement("button");
            chatButton.className = "conversation-item";
            chatButton.textContent = conversation.title;
            chatButton.title = conversation.title;

            if (Number(conversation.id) === Number(currentConversationId)) {
                chatButton.classList.add("active");
            }

            chatButton.addEventListener("click", () => {
                loadConversation(conversation.id);
            });

            // Delete button
            const deleteButton = document.createElement("button");
            deleteButton.className = "delete-conversation";
            deleteButton.textContent = "×";
            deleteButton.title = "Delete conversation";
            deleteButton.setAttribute("aria-label", "Delete conversation");

            deleteButton.addEventListener("click", async (event) => {
                event.stopPropagation();

                const confirmed = confirm(
                    `Are you sure you want to delete "${conversation.title}"?`
                );

                if (!confirmed) return;

                try {
                    const deleteResponse = await fetch(
                        `/conversations/${conversation.id}`,
                        { method: "DELETE" }
                    );

                    const result = await deleteResponse.json();

                    if (!deleteResponse.ok) {
                        throw new Error(result.error || "Could not delete chat.");
                    }

                    // If the deleted chat was open, reset the chat screen
                    if (
                        Number(currentConversationId) ===
                        Number(conversation.id)
                    ) {
                        currentConversationId = null;
                        chatContainer.replaceChildren();
                        showWelcome();
                    }

                    await loadConversations();

                } catch (error) {
                    console.error("Delete error:", error);
                    alert("Could not delete this conversation.");
                }
            });

            wrapper.appendChild(chatButton);
            wrapper.appendChild(deleteButton);

            conversationList.appendChild(wrapper);
        });

    } catch (error) {
        console.error("Could not load conversations:", error);
    }
}

// Load messages from a selected conversation.
async function loadConversation(conversationId) {
    try {
        const response = await fetch(`/conversations/${conversationId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Could not load conversation.");
        }

        currentConversationId = conversationId;

        chatContainer.replaceChildren();

        showChat();

        data.messages.forEach((message) => {
            createMessage(message.role, message.content);
        });

        await loadConversations();

    } catch (error) {
        console.error("Could not open conversation:", error);
        alert("Could not open this conversation.");
    }
}

// ========================================
// 1. Show or Hide Welcome Screen
// ========================================

function showChat() {
    welcomeScreen.style.display = "none";
    chatContainer.classList.add("active");
}

function showWelcome() {
    welcomeScreen.style.display = "";
    chatContainer.classList.remove("active");
}


// ========================================
// 2. Create a Chat Message
// ========================================

function createMessage(role, text) {
    const message = document.createElement("div");

    message.className = `message ${role}-message`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "👤" : "🐍";

    const content = document.createElement("div");
    content.className = "message-content";

    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = role === "user" ? "You" : "PythonBookAI";

    const messageText = document.createElement("div");
messageText.className = "message-text";

if (role === "assistant" && window.marked && window.DOMPurify) {
    const cleanedText = text.replace(/\\([#*_`~])/g, "$1");

    messageText.innerHTML = DOMPurify.sanitize(
        marked.parse(cleanedText)
    );
} else {
    messageText.textContent = text;
}

    content.appendChild(label);
    content.appendChild(messageText);

    message.appendChild(avatar);
    message.appendChild(content);

    chatContainer.appendChild(message);

    return {
        message,
        content,
        messageText
    };
}


// ========================================
// 3. Display Retrieved Sources
// ========================================

function displaySources(content, sources) {
    if (!Array.isArray(sources) || sources.length === 0) {
        return;
    }

    const sourcesBox = document.createElement("div");
    sourcesBox.className = "sources-box";

    const heading = document.createElement("h4");
    heading.textContent = "📚 Retrieved Sources";

    sourcesBox.appendChild(heading);

    sources.forEach((source) => {
        const item = document.createElement("div");
        item.className = "source-item";

        const bookTag = document.createElement("span");
        bookTag.className = "source-tag";
        bookTag.textContent =
            source.source || source.book || "Unknown book";

        const pageTag = document.createElement("span");
        pageTag.className = "source-tag";
        pageTag.textContent = `Page ${source.page ?? "Unknown"}`;

        item.appendChild(bookTag);
        item.appendChild(pageTag);

        sourcesBox.appendChild(item);
    });

    content.appendChild(sourcesBox);
}


// ========================================
// 4. Display Code Validation
// ========================================

function displayValidation(content, validation) {
    if (!validation || typeof validation !== "object") {
        return;
    }

    const issues = [];

    // Support common validation result formats.
    if (Array.isArray(validation.errors)) {
        issues.push(...validation.errors);
    }

    if (Array.isArray(validation.warnings)) {
        issues.push(...validation.warnings);
    }

    if (validation.valid === false) {
        issues.push("The generated code may contain syntax or other issues.");
    }

    if (issues.length === 0) {
        return;
    }

    const box = document.createElement("div");
    box.className = "validation-box warning";

    const heading = document.createElement("strong");
    heading.textContent = "⚠️ Code validation notes";

    const list = document.createElement("ul");
    list.style.margin = "8px 0 0 18px";

    issues.forEach((issue) => {
        const item = document.createElement("li");

        // Avoid inserting model-generated content as HTML.
        item.textContent = typeof issue === "string"
            ? issue
            : JSON.stringify(issue);

        list.appendChild(item);
    });

    box.appendChild(heading);
    box.appendChild(list);

    content.appendChild(box);
}


// ========================================
// 5. Loading Indicator
// ========================================

function showLoadingIndicator() {
    const loading = document.createElement("div");
    loading.className = "message assistant-message";
    loading.id = "loading-indicator";

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = "🐍";

    const content = document.createElement("div");
    content.className = "message-content";

    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = "PythonBookAI";

    const loadingText = document.createElement("div");
    loadingText.className = "loading-message";
    loadingText.textContent = "Searching your books and generating an answer ";

    const dots = document.createElement("span");
    dots.className = "loading-dots";

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement("span");
        dots.appendChild(dot);
    }

    loadingText.appendChild(dots);
    content.appendChild(label);
    content.appendChild(loadingText);

    loading.appendChild(avatar);
    loading.appendChild(content);

    chatContainer.appendChild(loading);

    return loading;
}


// ========================================
// 6. Send Question to Flask Backend
// ========================================

async function askQuestion(question) {
    const cleanedQuestion = question.trim();

    if (!cleanedQuestion) {
        questionInput.focus();
        return;
    }

    // Create a conversation if one is not already active.
    if (!currentConversationId) {
        try {
            await createConversation();
        } catch (error) {
            console.error("Could not create conversation:", error);
            alert("Could not start a new conversation. Please try again.");
            return;
        }
    }

    showChat();

    // Display the user's question.
    createMessage("user", cleanedQuestion);

    // Clear the input box.
    questionInput.value = "";
    questionInput.style.height = "auto";

    // Prevent multiple simultaneous requests.
    sendButton.disabled = true;
    questionInput.disabled = true;

    const loadingIndicator = showLoadingIndicator();

    // Keep the newest message visible.
    loadingIndicator.scrollIntoView({
        behavior: "smooth",
        block: "end"
    });

    try {
    const response = await fetch("/ask", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            question: cleanedQuestion,
            source: bookSelect ? bookSelect.value || null : null,
            conversation_id: currentConversationId
        })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.error || "The server could not process your question."
        );
    }
        // Remove the loading indicator.
        loadingIndicator.remove();

        // Display the AI's answer.
        const answerMessage = createMessage(
            "assistant",
            data.answer || "No answer was returned."
        );

        // Display the retrieved sources.
        displaySources(
            answerMessage.content,
            data.sources
        );

        // Display code validation notes when available.
        displayValidation(
            answerMessage.content,
            data.code_validation
        );
        // Refresh conversation titles in the sidebar.
        await loadConversations();
        answerMessage.message.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    } catch (error) {
        loadingIndicator.remove();

        const errorMessage = createMessage(
            "assistant",
            `Error: ${error.message}`
        );

        errorMessage.messageText.classList.add("error-message");

        console.error("PythonBookAI request failed:", error);

    } finally {
        sendButton.disabled = false;
        questionInput.disabled = false;
        questionInput.focus();
    }
}


// ========================================
// 7. Handle Form Submission
// ========================================

questionForm.addEventListener("submit", (event) => {
    event.preventDefault();
    askQuestion(questionInput.value);
});


// ========================================
// 8. Enter to Send, Shift+Enter for New Line
// ========================================

questionInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        questionForm.requestSubmit();
    }
});


// Automatically resize the question box.
questionInput.addEventListener("input", () => {
    questionInput.style.height = "auto";

    questionInput.style.height =
        Math.min(questionInput.scrollHeight, 160) + "px";
});


// ========================================
// 9. Suggested Questions
// ========================================

document.querySelectorAll(".suggestion-card").forEach((button) => {
    button.addEventListener("click", () => {
        const question = button.dataset.question;

        if (question) {
            askQuestion(question);
        }
    });
});


// ========================================
// 10. Start a New Question
// ========================================

newChatButton.addEventListener("click", () => {
    // Reset the active conversation.
    currentConversationId = null;

    // Clear previous messages.
    chatContainer.replaceChildren();

    // Reset input.
    questionInput.value = "";
    questionInput.style.height = "auto";

    // Show welcome screen.
    showWelcome();

    // Update conversation highlighting.
    loadConversations();

    questionInput.focus();
});
// ========================================
// 11. Initial Setup
// ========================================

showWelcome();
loadConversations();
console.log("PythonBookAI frontend loaded successfully.");
// ========================================
// 12. PDF UPLOAD
// ========================================

const uploadPdfButton = document.getElementById("upload-pdf-button");
const pdfUploadInput = document.getElementById("pdf-upload-input");
const uploadStatus = document.getElementById("upload-status");

if (uploadPdfButton && pdfUploadInput && uploadStatus) {

    // Open file picker
    uploadPdfButton.addEventListener("click", () => {
        pdfUploadInput.click();
    });

    // Handle selected PDF
    pdfUploadInput.addEventListener("change", async () => {

        const file = pdfUploadInput.files[0];

        if (!file) {
            return;
        }

        // Validate file extension
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            uploadStatus.textContent = "Please select a PDF file.";
            pdfUploadInput.value = "";
            return;
        }

        // Validate file size (maximum 50 MB)
        const maxSize = 50 * 1024 * 1024;

        if (file.size > maxSize) {
            uploadStatus.textContent = "File size must be below 50 MB.";
            pdfUploadInput.value = "";
            return;
        }

        // Prepare upload data
        const formData = new FormData();
        formData.append("file", file);

        uploadPdfButton.disabled = true;
        uploadStatus.textContent = "Uploading and indexing PDF...";

        try {

            const response = await fetch("/upload", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || "PDF upload failed."
                );
            }

            uploadStatus.textContent =
                data.message || "PDF uploaded successfully!";

            // Add newly uploaded PDF to book selector
            if (bookSelect && data.filename) {

                const existingOption = Array.from(
                    bookSelect.options
                ).find(option => option.value === data.filename);

                if (!existingOption) {

                    const option = document.createElement("option");

                    option.value = data.filename;
                    option.textContent = data.filename;

                    bookSelect.appendChild(option);
                }
            }

            console.log("PDF upload successful:", data);

        } catch (error) {

            console.error("PDF upload error:", error);

            uploadStatus.textContent = error.message;

        } finally {

            uploadPdfButton.disabled = false;
            pdfUploadInput.value = "";
        }
    });
}
// ========================================
// PDF SUMMARIZATION
// ========================================

const summarizeButton = document.getElementById("summarize-button");
const summarizeStatus = document.getElementById("summarize-status");
const summaryContainer = document.getElementById("summary-container");
const summaryContent = document.getElementById("summary-content");


summarizeButton.addEventListener("click", async function () {

    const filename = bookSelect.value;

    // Check PDF selection
    if (!filename) {
        summarizeStatus.textContent =
            "Please select a specific PDF, not All Books.";
        return;
    }

    try {

        // Disable button while processing
        summarizeButton.disabled = true;
        summarizeButton.textContent = "⏳ Generating Summary...";

        summarizeStatus.textContent =
            "Processing your PDF. This may take several minutes.";

        summaryContainer.hidden = false;

        summaryContent.textContent =
            "AI is reading and summarizing your document...";

        const response = await fetch("/summarize", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                filename: filename
            })

        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Summarization failed.");
        }

        // Display summary safely
        summaryContent.innerHTML = DOMPurify.sanitize(
            marked.parse(data.summary)
        );

        summarizeStatus.textContent =
            `Summary generated successfully! ${data.total_pages} pages processed.`;

    } catch (error) {

        console.error("Summarization error:", error);

        summarizeStatus.textContent = error.message;

        summaryContent.textContent =
            "Unable to generate the summary.";

    } finally {

        // Enable button again
        summarizeButton.disabled = false;
        summarizeButton.textContent = "📝 Summarize PDF";

    }

});
from database import (
    initialize_database,
    create_conversation,
    save_message,
    get_conversations,
    get_messages,
    delete_conversation
)

# Initialize database
initialize_database()

# 1. Create conversation
chat_id = create_conversation("Database Testing")
print("Conversation created:", chat_id)

# 2. Save messages
save_message(chat_id, "user", "What is Python?")
save_message(chat_id, "assistant", "Python is a programming language.")

print("\nMessages:")
print(get_messages(chat_id))

# 3. Get conversation list
print("\nConversations:")
print(get_conversations())

# 4. Delete test conversation
deleted = delete_conversation(chat_id)
print("\nTest conversation deleted:", deleted)
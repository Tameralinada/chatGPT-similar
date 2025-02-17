# Streamlit Chat Assistant

A simple chat assistant built with Streamlit and TinyLlama, featuring persistent chat history using SQLite.

## Features

- Chat with TinyLlama AI model
- Persistent chat history using SQLite database
- Multiple chat sessions support
- Example questions for quick start
- Copy message functionality
- Clear chat history option

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

## Project Structure

- `app.py`: Main Streamlit application
- `database.py`: Database models and operations
- `requirements.txt`: Project dependencies
- `chat_history.db`: SQLite database (created automatically)

## Usage

1. Start a new chat using the "New Chat" button
2. Type your message or click on example questions
3. View chat history in the sidebar
4. Clear chat history using the "Clear Chat" button
5. Copy messages using the clipboard button

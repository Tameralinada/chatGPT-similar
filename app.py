import streamlit as st
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from database import (
    Messages,
    save_message,
    get_chat_history,
    delete_chat,
    get_chat_folders
)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
if "model_loaded" not in st.session_state:
    st.session_state.model_loaded = False

# Initialize model and tokenizer
@st.cache_resource
def load_model():
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True
    )
    return model, tokenizer

def generate_response(question):
    """Generate a response using TinyLlama model"""
    try:
        if not st.session_state.model_loaded:
            with st.spinner("Loading AI model (this will only happen once)..."):
                model, tokenizer = load_model()
                st.session_state.model_loaded = True
        else:
            model, tokenizer = load_model()
        
        # Format the prompt for TinyLlama
        prompt = f"<human>: {question}\n<assistant>:"
        
        # Generate response
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs,
            max_length=512,
            num_return_sequences=1,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract only the assistant's response
        response = response.split("<assistant>:")[-1].strip()
        return response
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}"

# Page Configuration
st.set_page_config(
    page_title="AI Chat Assistant",
    page_icon="🤖",
    layout="wide"
)

# Sidebar
with st.sidebar:
    st.title("🤖 Chat History")
    
    # New Chat Button
    if st.button("New Chat", use_container_width=True):
        new_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.current_chat_id = new_chat_id
        st.session_state.chat_history = []
        st.rerun()
    
    # Chat History
    st.subheader("Recent Chats")
    
    # Get unique chat folders
    chat_folders = list(get_chat_folders())
    
    if not chat_folders:
        st.info("No chat history yet. Start a new conversation!")
    else:
        for folder in chat_folders:
            # Create a preview of the first message, truncate if too long
            preview = folder.question[:30] + "..." if len(folder.question) > 30 else folder.question
            formatted_time = folder.last_message.strftime("%Y-%m-%d")
            
            with st.expander(f"📁 {preview} ({formatted_time})"):
                messages = get_chat_history(chat_id=folder.chat_id)
                
                for msg in messages:
                    formatted_time = msg.timestamp.strftime("%Y-%m-%d | %I:%M %p")
                    st.write(f"**Q:** {msg.question[:50]}...")
                    col1, col2 = st.columns([0.9, 0.1])
                    with col1:
                        st.write(f"**A:** {msg.answer[:100]}...")
                    with col2:
                        if st.button("📋", key=f"copy_{msg.id}"):
                            st.write("Copied!")
                    st.write(f"*{formatted_time}*")
                    st.divider()

# Main Chat Interface
st.title("AI Powered Chat Assistant 🤖")
st.subheader("Simple Q&A Assistant")

# Example messages
examples = [
    "Tell me about artificial intelligence",
    "How does machine learning work?",
    "What are neural networks?",
]

# Display example messages
st.write("Try these examples:")
cols = st.columns(len(examples))
for idx, col in enumerate(cols):
    if col.button(examples[idx], use_container_width=True):
        st.session_state.current_question = examples[idx]
        
# Chat input
input_text = st.text_input("Type your message here", key="message_input", 
                          value=st.session_state.get('current_question', ''))

# Send and Clear buttons
col1, col2 = st.columns(2)

if col1.button("Send", use_container_width=True):
    if input_text:
        with st.spinner("Generating response..."):
            # Generate response
            response = generate_response(input_text)
            
            # Save to database
            save_message(
                question=input_text,
                answer=response,
                chat_id=st.session_state.current_chat_id
            )
            
            # Update session state
            st.session_state.chat_history.insert(0, {
                "question": input_text,
                "answer": response,
                "timestamp": datetime.now()
            })
            
            # Clear input
            st.session_state.current_question = ""
            st.rerun()

if col2.button("Clear Chat", use_container_width=True):
    if st.session_state.chat_history:  # Only if there's chat history
        delete_chat(st.session_state.current_chat_id)
        st.session_state.chat_history = []
        st.rerun()

# Display current chat
st.subheader("Current Chat")
for chat in st.session_state.chat_history:
    st.write(f"**You:** {chat['question']}")
    col1, col2 = st.columns([0.9, 0.1])
    with col1:
        st.write(f"**Assistant:** {chat['answer']}")
    with col2:
        st.button("📋", key=f"copy_current_{chat['timestamp']}")
    st.write(f"*{chat['timestamp'].strftime('%Y-%m-%d | %I:%M %p')}*")
    st.divider()

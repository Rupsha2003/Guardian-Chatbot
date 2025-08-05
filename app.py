# app.py

import streamlit as st
import os
import sys

# --- Robust Path Handling for Streamlit Cloud and Local ---
# Get the absolute path to the directory where app.py resides
current_dir = os.path.dirname(os.path.abspath(__file__))
# Add the project root to sys.path.
# This ensures that 'config', 'models', and 'utils' can be imported directly.
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the backend logic from your utils folder
# These imports now rely on the project_root being in sys.path
from models.embeddings import GuardianEmbeddings
from utils.rag_utils import load_and_chunk_document, create_vector_store, retrieve_relevant_info
from utils.web_search import perform_web_search
from utils.llm_generation import initialize_llm, generate_answer_from_context

# Import api_keys directly here, as app.py is at the root
import config.api_keys # New: Import the config module directly

# --- Setup the Streamlit UI and "Liquid Glass" CSS ---
st.set_page_config(layout="wide", page_title="Guardian Chatbot")

# Inject custom CSS for the "liquid glass" effect
def load_css(file_name):
    css_path = os.path.join(current_dir, file_name)
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.error(f"CSS file not found: {css_path}")

load_css("style.css")

st.markdown("<h1 class='liquid-title'>Guardian AI</h1>", unsafe_allow_html=True)
st.markdown("<p class='glass-box'>Your trusted assistant for fraud prevention and security knowledge. Powered by RAG and live web search.</p>", unsafe_allow_html=True)


# --- Initialize Session State and Backend Components ---
if "faiss_index" not in st.session_state:
    st.session_state.faiss_index = None
    st.session_state.document_chunks = None
    st.session_state.embeddings_model = None
    st.session_state.llm_model = None

    @st.cache_resource
    def setup_backend():
        st.write("Initializing backend components. This may take a moment...")
        embeddings_model = GuardianEmbeddings()

        # Get API keys using the functions from config.api_keys
        serper_key = config.api_keys.get_serper_api_key()
        gemini_key = config.api_keys.get_gemini_api_key()

        llm_model = initialize_llm(gemini_key) # Pass Gemini key
        if not llm_model:
            st.error("Failed to initialize the LLM model. Please check your API key and try again.")
            st.stop()
        
        knowledge_base_path = os.path.join(current_dir, "transactions_knowledge_base.txt")
        if not os.path.exists(knowledge_base_path):
            st.error(f"Error: The knowledge base file '{knowledge_base_path}' was not found.")
            st.stop()

        document_chunks = load_and_chunk_document(knowledge_base_path)
        faiss_index, _ = create_vector_store(document_chunks, embeddings_model)

        # Return serper_key as well, so it can be used later
        return embeddings_model, llm_model, faiss_index, document_chunks, serper_key

    st.session_state.embeddings_model, st.session_state.llm_model, st.session_state.faiss_index, st.session_state.document_chunks, st.session_state.serper_api_key = setup_backend()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# --- Sidebar for Response Mode and Chat Management ---
with st.sidebar:
    st.markdown("<h2 class='liquid-subtitle'>Chat Settings</h2>", unsafe_allow_html=True)
    
    response_mode = st.radio(
        "Response Mode:",
        ("Concise", "Detailed"),
        index=0,
        help="Choose between short, summarized replies or expanded, in-depth responses."
    )
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []


# --- Display Chat Messages ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --- Handle User Input ---
if prompt := st.chat_input("Ask a question about fraud, security, or anything else..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            is_search_query = any(keyword in prompt.lower() for keyword in ["search", "find", "who is", "what is", "tell me about"])
            
            final_answer = ""
            
            if is_search_query and not any(kw in prompt.lower() for kw in ["fraud", "security", "transaction", "phishing", "identity theft", "account takeover", "bnpl"]):
                st.info("Performing a live web search as requested.")
                # Pass serper_api_key to perform_web_search
                web_results = perform_web_search(prompt, st.session_state.serper_api_key)
                if web_results:
                    final_answer = generate_answer_from_context(st.session_state.llm_model, prompt, web_results, response_mode)
                else:
                    final_answer = "Sorry, I couldn't find any relevant web search results for your query."
            else:
                st.info("Searching local knowledge base...")
                retrieved_context = retrieve_relevant_info(prompt, st.session_state.faiss_index, st.session_state.document_chunks, st.session_state.embeddings_model)
                
                if retrieved_context and len(retrieved_context.strip()) > 50:
                    st.info("Generating a response from the knowledge base.")
                    final_answer = generate_answer_from_context(st.session_state.llm_model, prompt, retrieved_context, response_mode)
                else:
                    st.warning("No relevant information found in the local knowledge base or context was too short.")
                    st.info("Performing a web search as a fallback...")
                    # Pass serper_api_key to perform_web_search
                    web_results = perform_web_search(prompt, st.session_state.serper_api_key)
                    if web_results:
                        final_answer = generate_answer_from_context(st.session_state.llm_model, prompt, web_results, response_mode)
                    else:
                        final_answer = "Sorry, I couldn't find an answer in either the knowledge base or a web search."
            
            st.markdown(final_answer)

    st.session_state.messages.append({"role": "assistant", "content": final_answer})


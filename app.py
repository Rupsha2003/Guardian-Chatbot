# app.py

import streamlit as st
import os

# --- Import API Key Retrieval Functions ---
from config.api_keys import get_serper_api_key, get_gemini_api_key

# --- Import Backend Logic ---
from models.embeddings import GuardianEmbeddings
from utils.rag_utils import load_and_chunk_document, create_vector_store, retrieve_relevant_info
from utils.web_search import perform_web_search
from utils.llm_generation import initialize_llm, generate_answer_from_context


# --- Setup Streamlit Page Configuration and CSS ---
st.set_page_config(layout="wide", page_title="Guardian Chatbot")

# Get the absolute path to the directory where app.py resides
current_dir = os.path.dirname(os.path.abspath(__file__))

# Inject custom CSS for the "liquid glass" effect
def load_css(file_name):
    css_path = os.path.join(current_dir, file_name)
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.error(f"CSS file not found: {css_path}")

load_css("style.css") # Load the custom CSS


# --- Initialize Session State and Backend Components ---
# This ensures heavy components are loaded only once
if "faiss_index" not in st.session_state:
    st.session_state.faiss_index = None
    st.session_state.document_chunks = None
    st.session_state.embeddings_model = None
    st.session_state.llm_model = None
    st.session_state.serper_api_key = None # Store serper key in session state

    @st.cache_resource
    def setup_backend():
        st.write("Initializing backend components. This may take a moment...")
        embeddings_model = GuardianEmbeddings()

        serper_key = get_serper_api_key()
        gemini_key = get_gemini_api_key()

        llm_model = initialize_llm()
        if not llm_model:
            st.error("Failed to initialize the LLM model. Please check your API key and try again.")
            st.stop()
        
        knowledge_base_path = os.path.join(current_dir, "transactions_knowledge_base.txt")
        if not os.path.exists(knowledge_base_path):
            st.error(f"Error: The knowledge base file '{knowledge_base_path}' was not found.")
            st.stop()

        document_chunks = load_and_chunk_document(knowledge_base_path)
        faiss_index, _ = create_vector_store(document_chunks, embeddings_model)

        return embeddings_model, llm_model, faiss_index, document_chunks, serper_key

    st.session_state.embeddings_model, st.session_state.llm_model, \
    st.session_state.faiss_index, st.session_state.document_chunks, \
    st.session_state.serper_api_key = setup_backend()

# Initialize chat history and current page if not already set
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"


# --- Page Navigation Functions ---
def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

# --- Home Page Function ---
def home_page():
    st.markdown("<h1 class='liquid-title home-title'>Guardian AI</h1>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class='glass-box home-welcome-container'>
            <p class='home-welcome-text'>Welcome to Guardian AI, your personal assistant for financial security and fraud prevention.</p>
            <p class='home-tagline'>Empowering you with knowledge to protect your financial well-being.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='home-buttons-container'>", unsafe_allow_html=True)
    
    # Use columns for side-by-side buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Chatting with Guardian AI", key="start_chat_button"):
            navigate_to("chat")
    with col2:
        if st.button("About the Creator", key="about_creator_button"):
            navigate_to("about_creator")
        
    st.markdown("</div>", unsafe_allow_html=True)


# --- Chat Page Function ---
def chat_page():
    st.markdown("<h1 class='liquid-title'>Guardian AI Chat</h1>", unsafe_allow_html=True)
    st.markdown("<p class='glass-box description-box'>Ask me anything about financial security, fraud prevention, or general knowledge. I'm here to help!</p>", unsafe_allow_html=True)

    # Sidebar for Response Mode and Chat Management
    with st.sidebar:
        st.markdown("<h2 class='liquid-subtitle'>Chat Settings</h2>", unsafe_allow_html=True)
        
        # Floating slide for Response Mode
        st.markdown("<div class='liquid-radio-container'>", unsafe_allow_html=True)
        response_mode = st.radio(
            "Response Mode:",
            ("Concise", "Detailed"),
            index=0,
            horizontal=True, # Make it horizontal for a slide-like appearance
            help="Choose between short, summarized replies or expanded, in-depth responses."
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun() # Rerun to clear messages and refresh
        
        st.markdown("---") # Separator
        if st.button("Back to Home", key="back_to_home_from_chat"):
            navigate_to("home")
        if st.button("Go to About Creator", key="about_from_chat"):
            navigate_to("about_creator")


    # Display Chat Messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle User Input
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
                    web_results = perform_web_search(prompt)
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
                        web_results = perform_web_search(prompt)
                        if web_results:
                            final_answer = generate_answer_from_context(st.session_state.llm_model, prompt, web_results, response_mode)
                        else:
                            final_answer = "Sorry, I couldn't find an answer in either the knowledge base or a web search."
                
                st.markdown(final_answer)

        st.session_state.messages.append({"role": "assistant", "content": final_answer})


# --- About Creator Page Function ---
def about_creator_page():
    st.markdown("<h1 class='liquid-title'>About the Creator</h1>", unsafe_allow_html=True)
    
    # Updated image path to NEWPHOTO.jpg
    image_path = "NEWPHOTO.jpg" 
    
    st.markdown(f"""
        <div class='glass-box about-creator-content'>
            <div class='circular-image-container'>
                <img src='{image_path}' class='circular-image' alt='Rupsha Das'>
            </div>
            <p>Hello! I'm Rupsha Das, the creator of Guardian AI. My goal was to build an intelligent and accessible tool that empowers individuals with knowledge to protect themselves against financial fraud and enhance their digital security. This project combines advanced AI techniques like Retrieval-Augmented Generation (RAG) with a user-friendly interface to make complex information easy to understand and act upon.</p>
            <p>This chatbot is designed to provide you with quick, reliable information on various types of fraud, security protocols, and steps to take if you become a victim. It leverages a comprehensive internal knowledge base and can perform real-time web searches for the latest information.</p>
            <p>I believe that awareness is the first step towards prevention, and I hope Guardian AI serves as a valuable resource in your journey towards better financial safety.</p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar for Navigation
    with st.sidebar:
        st.markdown("<h2 class='liquid-subtitle'>Navigation</h2>", unsafe_allow_html=True)
        if st.button("Back to Home", key="back_to_home_from_about"):
            navigate_to("home")
        if st.button("Go to Chat", key="chat_from_about"):
            navigate_to("chat")


# --- Main App Logic (Page Routing) ---
if st.session_state.current_page == "home":
    home_page()
elif st.session_state.current_page == "chat":
    chat_page()
elif st.session_state.current_page == "about_creator":
    about_creator_page()
# app.py

import streamlit as st
import os
import io # For handling file-like objects

# --- Import API Key Retrieval Functions ---
# These functions are assumed to be correctly defined in config/api_keys.py
# and fetch keys from Streamlit secrets.
from config.api_keys import get_serper_api_key, get_gemini_api_key

# --- Import Backend Logic ---
# These modules are assumed to be correctly structured and accessible.
from models.embeddings import GuardianEmbeddings
from utils.rag_utils import load_and_chunk_document, create_vector_store, retrieve_relevant_info
from utils.web_search import perform_web_search
from utils.llm_generation import initialize_llm, generate_answer_from_context

# --- File Processing Libraries ---
# Import these directly here as they are used in app.py for file handling
try:
    from pypdf import PdfReader
except ImportError:
    st.warning("PyPDF2 or pypdf not found. PDF processing will be disabled.")
    PdfReader = None

try:
    from docx import Document
except ImportError:
    st.warning("python-docx not found. DOCX processing will be disabled.")
    Document = None


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
# This ensures heavy components are loaded only once and cached.
if "faiss_index" not in st.session_state:
    st.session_state.faiss_index = None
    st.session_state.document_chunks = None
    st.session_state.embeddings_model = None
    st.session_state.llm_model = None
    st.session_state.serper_api_key = None # Store serper key in session state
    st.session_state.uploaded_faiss_index = None # New: For uploaded file's vector store
    st.session_state.uploaded_document_chunks = None # New: For uploaded file's chunks
    st.session_state.uploaded_file_name = None # To track the name of the uploaded file

    @st.cache_resource
    def setup_backend():
        st.write("Initializing backend components. This may take a moment...")
        embeddings_model = GuardianEmbeddings()

        serper_key = get_serper_api_key()
        gemini_key = get_gemini_api_key()

        llm_model = initialize_llm() # initialize_llm now fetches key internally
        if not llm_model:
            st.error("Failed to initialize the LLM model. Please check your API key and try again.")
            st.stop()
        
        knowledge_base_path = os.path.join(current_dir, "transactions_knowledge_base.txt")
        if not os.path.exists(knowledge_base_path):
            st.error(f"Error: The knowledge base file '{knowledge_base_path}' was not found.")
            st.stop()

        document_chunks = load_and_chunk_document(file_path=knowledge_base_path) # Pass file_path explicitly
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


# --- File Processing Function ---
def process_uploaded_file(uploaded_file_obj, embeddings_model):
    """Processes an uploaded file, extracts text, and creates a new vector store."""
    file_content = ""
    file_type = uploaded_file_obj.type

    if "text" in file_type:
        file_content = uploaded_file_obj.read().decode("utf-8")
    elif "pdf" in file_type and PdfReader:
        try:
            reader = PdfReader(io.BytesIO(uploaded_file_obj.read()))
            for page in reader.pages:
                file_content += page.extract_text() + "\n"
        except Exception as e:
            st.error(f"Error reading PDF file: {e}")
            return None, None
    elif "document" in file_type or "wordprocessingml" in file_type and Document: # For .docx
        try:
            doc = Document(io.BytesIO(uploaded_file_obj.read()))
            for para in doc.paragraphs:
                file_content += para.text + "\n"
        except Exception as e:
            st.error(f"Error reading DOCX file: {e}")
            return None, None
    else:
        st.warning(f"Unsupported file type: {file_type}. Please upload a .txt, .pdf, or .docx file.")
        return None, None

    if file_content:
        with st.spinner("Processing uploaded document..."):
            uploaded_chunks = load_and_chunk_document(file_content=file_content) # Pass content directly
            
            if uploaded_chunks:
                uploaded_faiss_index, _ = create_vector_store(uploaded_chunks, embeddings_model)
                st.success(f"Successfully processed '{uploaded_file_obj.name}' with {len(uploaded_chunks)} chunks.")
                return uploaded_faiss_index, uploaded_chunks
            else:
                st.error("Failed to chunk content from uploaded file.")
                return None, None
    return None, None


# --- Page Navigation Functions ---
def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

# --- Home Page Function ---
def home_page():
    # Updated title text
    st.markdown("<h1 class='liquid-title home-title'>GUARDIAN AI CHATBOT</h1>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class='glass-box home-welcome-container'>
            <p class='home-welcome-text'>Welcome to Guardian AI, your personal assistant for financial security and fraud prevention.</p>
            <p class='home-tagline'>Empowering you with knowledge to protect your financial well-being.</p>
        </div>
    """, unsafe_allow_html=True)

    # Reverted to two columns for left/right button placement
    st.markdown("<div class='home-buttons-container'>", unsafe_allow_html=True)
    
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
    # Changed class to 'yellow-glass-box' for the description
    st.markdown("<p class='yellow-glass-box description-box'>Ask me about financial security, fraud prevention or anything that's on your mind. I'm here to help!</p>", unsafe_allow_html=True)

    # --- File Uploader Section (MOVED TO SIDEBAR) ---
    with st.sidebar:
        st.markdown("---") # Separator
        st.markdown("<h2 class='liquid-subtitle'>Document Context</h2>", unsafe_allow_html=True)
        st.markdown("<div class='file-uploader-sidebar-container glass-box'>", unsafe_allow_html=True) # New class for sidebar uploader
        uploaded_file = st.file_uploader(
            "Upload a document for context (TXT, PDF, DOCX)",
            type=["txt", "pdf", "docx"],
            key="file_uploader_sidebar" # Changed key for sidebar uploader
        )

        if uploaded_file is not None:
            # Check if a new file is uploaded or if the existing one is different
            if st.session_state.get('uploaded_file_hash') != hash(uploaded_file.read()):
                uploaded_file.seek(0) # Reset file pointer after reading hash
                st.session_state.uploaded_file_hash = hash(uploaded_file.read())
                uploaded_file.seek(0) # Reset file pointer again for actual processing

                uploaded_index, uploaded_chunks = process_uploaded_file(uploaded_file, st.session_state.embeddings_model)
                if uploaded_index and uploaded_chunks:
                    st.session_state.uploaded_faiss_index = uploaded_index
                    st.session_state.uploaded_document_chunks = uploaded_chunks
                    st.session_state.uploaded_file_name = uploaded_file.name
                else:
                    st.session_state.uploaded_faiss_index = None
                    st.session_state.uploaded_document_chunks = None
                    st.session_state.uploaded_file_name = None
                st.rerun() # Rerun to update state immediately
            
            if st.session_state.uploaded_faiss_index:
                st.info(f"Using context from: {st.session_state.uploaded_file_name}")
        elif st.session_state.uploaded_faiss_index:
            st.info(f"Currently using context from previously uploaded: {st.session_state.uploaded_file_name}")
        else:
            st.info("Using context from default knowledge base.")

        if st.session_state.uploaded_faiss_index and st.button("Clear Uploaded Data", key="clear_uploaded_data_sidebar"): # Changed key
            st.session_state.uploaded_faiss_index = None
            st.session_state.uploaded_document_chunks = None
            st.session_state.uploaded_file_name = None
            st.session_state.uploaded_file_hash = None # Clear hash too
            st.success("Uploaded data cleared. Reverting to default knowledge base.")
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True) # End file-uploader-sidebar-container
        st.markdown("---") # Separator for navigation

        st.markdown("<h2 class='liquid-subtitle'>Chat Settings</h2>", unsafe_allow_html=True)
        # This radio button remains in the main area near the chat input
        # st.markdown("<div class='liquid-radio-container'>", unsafe_allow_html=True)
        # response_mode = st.radio(
        #     "Response Mode:",
        #     ("Concise", "Detailed"),
        #     index=0,
        #     horizontal=True,
        #     key="response_mode_radio_sidebar", # Original sidebar radio
        #     help="Choose between short, summarized replies or expanded, in-depth responses."
        # )
        # st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun() # Rerun to clear messages and refresh
        
        st.markdown("---") # Separator
        st.markdown("<h2 class='liquid-subtitle'>Navigation</h2>", unsafe_allow_html=True)
        if st.button("Back to Home", key="back_to_home_from_chat"):
            navigate_to("home")
        if st.button("Go to About Creator", key="about_from_chat"):
            navigate_to("about_creator")


    # --- Response Mode Buttons (Near Chat Input - REMAINS IN MAIN AREA) ---
    st.markdown("<div class='liquid-radio-container-main'>", unsafe_allow_html=True)
    response_mode = st.radio(
        "Response Mode:",
        ("Concise", "Detailed"),
        index=0,
        horizontal=True, # Make it horizontal for a slide-like appearance
        key="response_mode_radio_main", # Unique key for this radio button in main area
        help="Choose between short, summarized replies or expanded, in-depth responses."
    )
    st.markdown("</div>", unsafe_allow_html=True)


    # Display Chat Messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle User Input
    if prompt := st.chat_input("Ask a question about fraud, security, or anything that's on your mind.."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Determine which vector store to use
                current_faiss_index = st.session_state.uploaded_faiss_index if st.session_state.uploaded_faiss_index else st.session_state.faiss_index
                current_document_chunks = st.session_state.uploaded_document_chunks if st.session_state.uploaded_document_chunks else st.session_state.document_chunks

                is_search_query = any(keyword in prompt.lower() for keyword in ["search", "find", "who is", "what is", "tell me about"])
                
                final_answer = ""
                
                # Prioritize web search for general knowledge questions not covered by local KB
                if is_search_query and not any(kw in prompt.lower() for kw in ["fraud", "security", "transaction", "phishing", "identity theft", "account takeover", "bnpl"]):
                    st.info("Performing a live web search as requested.")
                    web_results = perform_web_search(prompt)
                    if web_results:
                        final_answer = generate_answer_from_context(st.session_state.llm_model, prompt, web_results, response_mode)
                    else:
                        final_answer = "Sorry, I couldn't find any relevant web search results for your query."
                else:
                    st.info("Searching relevant context...")
                    # Use the dynamically selected index and chunks
                    retrieved_context = retrieve_relevant_info(prompt, current_faiss_index, current_document_chunks, st.session_state.embeddings_model)
                    
                    if retrieved_context and len(retrieved_context.strip()) > 50:
                        st.info("Generating a response from the provided context.")
                        final_answer = generate_answer_from_context(st.session_state.llm_model, prompt, retrieved_context, response_mode)
                    else:
                        st.warning("No relevant information found in the provided context.")
                        st.info("Performing a web search as a fallback...")
                        web_results = perform_web_search(prompt)
                        if web_results:
                            final_answer = generate_answer_from_context(st.session_state.llm_model, prompt, web_results, response_mode)
                        else:
                            final_answer = "Sorry, I couldn't find an answer in either the provided context or a web search."
                
                st.markdown(final_answer)

        st.session_state.messages.append({"role": "assistant", "content": final_answer})


# --- About Creator Page Function ---
def about_creator_page():
    st.markdown("<h1 class='liquid-title'>About the Creator</h1>", unsafe_allow_html=True)
    
    # Use the raw GitHub content URL for the image
    # IMPORTANT: Ensure NEWPHOTO.jpg is in the root of your GitHub repo
    image_path = "https://raw.githubusercontent.com/Rupsha2003/Guardian-Chatbot/main/NEWPHOTO.jpg"
    
    st.markdown(f"""
        <div class='glass-box about-creator-content'>
            <div class='circular-image-container'>
                <img src='{image_path}' class='circular-image' alt='Rupsha Das'>
            </div>
            <p>Hello! I'm Rupsha Das, the creator of Guardian AI. My goal was to build an intelligent and accessible tool that empowers individuals with knowledge to protect themselves against financial fraud and enhance their digital security. This project combines advanced AI techniques like Retrieval-Augmented Generation (RAG) with a user-friendly interface to make complex information easy to understand and act upon.</p>
            <p>This chatbot is designed to provide you with quick, reliable information on various types of fraud, security protocols, and steps to take if you become a victim. It leverages a comprehensive internal knowledge base and can perform real-time web searches for the latest information.</p>
            <p>I believe that awareness is the first step towards prevention, and I hope Guardian AI serves as a valuable resource in your journey towards better financial safety.</p>
            <p> Contact me - rups.das.2003@gmail.com </p>
            </div>
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


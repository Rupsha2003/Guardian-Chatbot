Guardian AI Chatbot

Your Personal Assistant for Financial Security and Fraud Prevention

Introduction
Guardian AI is an intelligent chatbot designed to empower users with quick, reliable information on financial security, fraud prevention, and general knowledge. Built with Streamlit, it offers an intuitive and visually appealing "liquid glass" user interface. The chatbot leverages a sophisticated Retrieval-Augmented Generation (RAG) system for in-depth knowledge from a local database and seamlessly integrates real-time web search for up-to-the-minute information.
Whether you're looking for tips to protect yourself from scams, understanding complex security protocols, or simply need a quick answer to a general query, Guardian AI is here to help you navigate the digital landscape safely.

Features
Financial Security & Fraud Prevention: Access a comprehensive knowledge base on various types of fraud (phishing, identity theft, account takeover, BNPL fraud), security protocols, and steps to take if you become a victim.

Retrieval-Augmented Generation (RAG): Efficiently retrieves relevant information from a local knowledge base (transactions_knowledge_base.txt) using advanced embedding models and FAISS vector search.

Real-time Web Search: Integrates with the Serper API to perform live web searches for queries outside the local knowledge base, ensuring up-to-date and broad information.

Custom Document Context (NEW!): Beyond its built-in knowledge base, Guardian AI now allows you to upload your own documents (in .txt, .pdf, or .docx formats). This enables the chatbot to provide answers and insights based on the specific content you provide, making it a versatile tool for various information retrieval needs.

Dual Response Modes: Choose between "Concise" (short, summarized replies) and "Detailed" (expanded, in-depth responses) to tailor the chatbot's output to your needs.

Sleek "Liquid Glass" UI: A modern and elegant user interface built with Streamlit and custom CSS, featuring blurred glass effects, vibrant blue accents, and a floating background animation.

Multi-Page Navigation: A structured application with dedicated pages for:
Home: Introduction to Guardian AI and quick access buttons.
Chat: The main interactive chatbot interface.
About Creator: Information about the developer, Rupsha Das, and the project's vision.

Screenshots

Homepage:
<img width="1912" height="908" alt="image" src="https://github.com/user-attachments/assets/a41b71a8-64ec-4d16-b021-b35d99de34ed" />


Chat Interface:
<img width="1918" height="875" alt="image" src="https://github.com/user-attachments/assets/09af8eef-88a3-4289-a8b3-08c87a777c74" />

<img width="1918" height="780" alt="image" src="https://github.com/user-attachments/assets/f623702a-f875-495f-ab1f-5d72e169bc64" />



About Creator Page:
<img width="1916" height="812" alt="image" src="https://github.com/user-attachments/assets/f52d8d49-80ee-4541-b1c5-80d21631c27b" />



📁 Project Structure
Guardian-Chatbot/
├── .streamlit/
│   └── secrets.toml        # Securely stores API keys for local development
├── config/
│   ├── __init__.py         # Makes 'config' a Python package
│   └── api_keys.py         # Functions to retrieve API keys
├── models/
│   ├── __init__.py         # Makes 'models' a Python package
│   └── embeddings.py       # Handles text embedding model (SentenceTransformer)
├── utils/
│   ├── __init__.py         # Makes 'utils' a Python package
│   ├── llm_generation.py   # Initializes LLM and generates responses
│   ├── rag_utils.py        # Loads, chunks documents, creates/searches vector store
│   └── web_search.py       # Performs real-time web searches via Serper API
├── app.py                  # Main Streamlit application file (entry point)
├── requirements.txt        # Lists all Python dependencies
├── style.css               # Custom CSS for the "liquid glass" UI
├── transactions_knowledge_base.txt # Your local knowledge base document
└── NEWPHOTO.jpg            # Your profile picture for "About Creator" page

Technologies Used

Python 3.10+
Streamlit: For building interactive web applications.
Google Gemini API (gemini-1.5-flash): For large language model capabilities.
Serper API: For real-time web search integration.
LangChain: Framework for developing applications powered by language models.
langchain-community: For document loaders (TextLoader) and vector stores (FAISS).
langchain-text-splitters: For text splitting (RecursiveCharacterTextSplitter).
Sentence Transformers: For generating embeddings (used by GuardianEmbeddings).
FAISS (Facebook AI Similarity Search): For efficient similarity search and vector storage.
Requests: For making HTTP requests to APIs.

 Implementation Details
 
1. Retrieval-Augmented Generation (RAG)
   
The chatbot utilizes a RAG architecture to provide accurate and context-aware responses.
Knowledge Base: Information from transactions_knowledge_base.txt is loaded and split into manageable chunks using RecursiveCharacterTextSplitter.
Embeddings: SentenceTransformer (via models/embeddings.py) converts these text chunks into numerical vector representations.
Vector Store: FAISS creates an efficient index of these embeddings, enabling fast similarity searches.
Retrieval: When a user asks a question, the most relevant chunks from the knowledge base are retrieved based on the semantic similarity to the query.

3. Real-time Web Search
   
For queries that cannot be adequately answered by the local knowledge base, the chatbot intelligently falls back to a real-time web search.
Serper API Integration: utils/web_search.py interacts with the Serper API to perform Google searches.
Context Augmentation: The snippets from the web search results are then passed to the LLM as additional context.

5. Large Language Model (LLM)
   
Google Gemini 1.5 Flash: The core of the chatbot's intelligence, responsible for understanding user queries and generating human-like responses.
Contextual Generation: The LLM synthesizes information from either the retrieved knowledge base chunks or web search results to formulate its answers.
Response Modes: The utils/llm_generation.py module handles the prompt engineering to produce "Concise" or "Detailed" responses based on user selection.

7. User Interface (UI)
8. 
Streamlit: Provides the framework for the interactive web application.
Custom CSS (style.css): Implements the "liquid glass" design, featuring:
Transparent, blurred elements (titles, content boxes, sidebar, chat input).
Vibrant blue color palette.
Subtle floating background animations for a dynamic feel.
Custom styling for buttons and radio buttons (floating slide effect).

9. Multi-Page Navigation
The application uses Streamlit's st.session_state to manage navigation between three distinct pages:

Home Page: The landing page introducing Guardian AI.
Chat Page: The primary interaction interface for the chatbot.
About Creator Page: Dedicated section providing information about the developer, Rupsha Das, and the project's mission, complete with a circular profile picture.

Setup and Local Development
To run this project locally, follow these steps:

Clone the repository:

git clone https://github.com/Rupsha2003/Guardian-Chatbot.git
cd Guardian-Chatbot

Create a Python Virtual Environment:
python -m venv venv

Activate the Virtual Environment:

On Windows (Command Prompt):
.\venv\Scripts\activate

On macOS/Linux (Bash/Zsh):
source venv/bin/activate

Install Dependencies:
pip install -r requirements.txt

Set Up API Keys:

Create a folder named .streamlit in your project's root directory.
Inside .streamlit, create a file named secrets.toml.
Add your API keys to secrets.toml like this:

SERPER_API_KEY = "YOUR_SERPER_API_KEY_HERE"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

Replace "YOUR_SERPER_API_KEY_HERE" and "YOUR_GEMINI_API_KEY_HERE" with your actual API keys.
Run the Streamlit App:
streamlit run app.py
Your app should open in your default web browser.

 Deployment on Streamlit Cloud
 
Ensure all files are pushed to your GitHub repository.
Verify NEWPHOTO.jpg is in the root directory of your GitHub repo.
Ensure requirements.txt is up-to-date with all dependencies.
Make sure __init__.py files are in config/, models/, and utils/.
Go to Streamlit Cloud: https://share.streamlit.io/ and log in with your GitHub account.
Click "New app" and connect to your Rupsha2003/Guardian-Chatbot repository.
Crucially, add your API keys as secrets in the "Advanced settings" or "Secrets" section of the deployment dialog:

SERPER_API_KEY = "YOUR_SERPER_API_KEY_HERE"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

Click "Deploy!" and monitor the logs.

Contact -

For any questions or feedback, feel free to contact the creator:

Rupsha Das

Email: rups.das.2003@gmail.comAuthor


Building intelligent solutions to empower and protect.

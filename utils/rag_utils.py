# File: utils/rag_utils.py

import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter # Corrected import for modularized LangChain
from langchain_community.vectorstores import FAISS
from models.embeddings import GuardianEmbeddings

# LangChain Document class for creating documents from text
from langchain.docstore.document import Document as LangchainDocument


def load_and_chunk_document(file_path=None, file_content=None):
    """
    Loads a document from the given file path or processes raw text content,
    then splits it into chunks.
    """
    documents = []
    if file_path:
        try:
            loader = TextLoader(file_path)
            documents = loader.load()
            print(f"Document loaded from path: {file_path}")
        except Exception as e:
            print(f"Error loading document from path '{file_path}': {e}")
            return []
    elif file_content:
        # Create a Langchain Document object from the raw text content
        documents = [LangchainDocument(page_content=file_content, metadata={"source": "uploaded_file"})]
        print("Document created from uploaded content.")
    else:
        print("No file path or content provided for chunking.")
        return []

    if not documents:
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Document split into {len(chunks)} chunks.")
    return chunks

def create_vector_store(document_chunks, embeddings_model):
    """
    Creates a FAISS vector store from document chunks and embeddings.
    """
    if not document_chunks:
        print("No document chunks to create vector store.")
        return None, None
    try:
        vector_store = FAISS.from_documents(document_chunks, embeddings_model)
        print("FAISS vector store created successfully.")
        return vector_store, embeddings_model
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return None, None

def retrieve_relevant_info(query, faiss_index, document_chunks, embeddings_model, num_chunks=3):
    """
    Retrieves the most relevant information from the FAISS index based on a query.

    Args:
        query (str): The user's query.
        faiss_index: The FAISS vector store.
        document_chunks (list): The original list of document chunks.
        embeddings_model: The embeddings model used.
        num_chunks (int): The number of top relevant chunks to retrieve.

    Returns:
        str: A concatenated string of the relevant document chunks.
    """
    if not faiss_index:
        print("FAISS index not initialized.")
        return ""

    try:
        num_chunks = int(num_chunks) 
        
        docs_and_scores = faiss_index.similarity_search_with_score(query, k=num_chunks)
        
        retrieved_texts = []
        if docs_and_scores:
            print(f"Retrieved {len(docs_and_scores)} relevant chunks from the knowledge base.")
            for doc, score in docs_and_scores:
                retrieved_texts.append(doc.page_content)
        else:
            print("No relevant chunks found in the knowledge base.")
            
        return "\n\n".join(retrieved_texts)
    except Exception as e:
        print(f"Error retrieving relevant info: {e}")
        return ""


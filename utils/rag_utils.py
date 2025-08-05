# File: utils/rag_utils.py

import faiss
import numpy as np

def load_and_chunk_document(file_path, chunk_size=500, overlap=50):
    """
    Loads a text document and splits it into smaller, overlapping chunks.

    Args:
        file_path (str): The path to the document file.
        chunk_size (int): The number of characters in each chunk.
        overlap (int): The number of overlapping characters between chunks.

    Returns:
        list of str: A list of text chunks.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []

    chunks = []
    start = 0
    while start < len(content):
        end = start + chunk_size
        chunks.append(content[start:end])
        start += (chunk_size - overlap)
    
    return chunks

def create_vector_store(chunks, embeddings_model):
    """
    Creates a FAISS vector index from document chunks and their embeddings.

    Args:
        chunks (list of str): The text chunks from the document.
        embeddings_model: An instance of the embedding model class.

    Returns:
        tuple: A tuple containing the FAISS index and the list of text chunks.
    """
    if not chunks:
        print("Warning: No chunks to process. Returning empty store.")
        return None, []

    print("Creating vector embeddings for the knowledge base...")
    embeddings = embeddings_model.embed_text(chunks)
    
    # Initialize a FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    
    print("Vector store created and populated with document chunks.")
    return index, chunks

def retrieve_relevant_info(query, index, chunks, embeddings_model, k=3):
    """
    Retrieves the top-k most relevant text chunks for a given query.

    Args:
        query (str): The user's query.
        index: The FAISS vector index.
        chunks (list of str): The list of original text chunks.
        embeddings_model: An instance of the embedding model class.
        k (int): The number of relevant chunks to retrieve.

    Returns:
        str: A single string combining the retrieved relevant chunks.
    """
    if index is None or not chunks:
        return "No knowledge base available for retrieval."

    query_embedding = embeddings_model.embed_text([query])
    distances, indices = index.search(query_embedding, k)
    
    relevant_chunks = [chunks[i] for i in indices[0]]
    
    print(f"Retrieved {len(relevant_chunks)} relevant chunks from the knowledge base.")
    return "\n\n".join(relevant_chunks)
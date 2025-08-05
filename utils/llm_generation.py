# File: utils/llm_generation.py

import google.generativeai as genai
# Import the config.api_keys module
import config.api_keys # Changed import

def initialize_llm():
    """Initializes and returns the Google Gemini Pro model."""
    try:
        # Access the function via the imported module
        GEMINI_API_KEY = config.api_keys.get_gemini_api_key()
        if not GEMINI_API_KEY:
            print("Error: GEMINI_API_KEY is not set. Please check your .streamlit/secrets.toml or Streamlit Cloud secrets.")
            return None
            
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash') # Using gemini-1.5-flash as discussed
        print("Google Gemini-1.5-flash model initialized successfully.")
        return model
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")
        return None

def generate_answer_from_context(model, query, context, response_mode="Concise"):
    """
    Generates a coherent answer using an LLM based on a query and retrieved context.
    
    Args:
        model: The initialized GenerativeModel instance.
        query (str): The user's original query.
        context (str): The text chunks retrieved from the knowledge base.
        response_mode (str): The desired response mode ('Concise' or 'Detailed').

    Returns:
        str: A human-like, conversational response.
    """
    if not model or not context:
        return "I'm sorry, I don't have enough information to answer that question."

    if response_mode.lower() == "detailed":
        prompt_instruction = "Give a detailed, in-depth, and expanded response based on the context. Do not use any outside information."
    else:
        prompt_instruction = "Give a short, concise, and summarized answer based on the context. Do not use any outside information."

    prompt = f"""
    You are a helpful assistant. {prompt_instruction}
    If the context does not contain the answer, say that you don't have enough information.

    Context:
    {context}

    Question: {query}
    Answer:
    """

    try:
        response = model.generate_content(prompt)
        if isinstance(response.text, str):
            return response.text
        return "".join([part.text for part in response.parts])

    except Exception as e:
        print(f"Error generating content: {e}")
        return f"I encountered an error while trying to generate a response: {e}"

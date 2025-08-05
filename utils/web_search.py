# File: utils/web_search.py

import requests
import json
import os
# Removed: from config.api_keys import get_serper_api_key

def perform_web_search(query, serper_api_key, num_results=3): # Added serper_api_key argument
    """
    Performs a real-time web search using the Serper API.

    Args:
        query (str): The search query.
        serper_api_key (str): The Serper API key.
        num_results (int): The number of search results to return.

    Returns:
        str: A formatted string containing the titles, snippets, and links of the top search results.
             Returns an empty string if the search fails.
    """
    if not serper_api_key: # Use the passed argument
        print("Error: SERPER_API_KEY is not provided.")
        return "Search functionality is not configured."
    
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': serper_api_key, # Use the passed argument
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status() # Raise an exception for bad status codes
        
        search_results = response.json()
        
        results_text = []
        if 'organic' in search_results and search_results['organic']:
            print(f"Web search for '{query}' successful. Found {len(search_results['organic'])} results.")
            for i, result in enumerate(search_results['organic'][:num_results]):
                title = result.get('title', 'No Title')
                snippet = result.get('snippet', 'No Snippet')
                link = result.get('link', 'No Link')
                results_text.append(f"Result {i+1}:\nTitle: {title}\nSnippet: {snippet}\nLink: {link}\n")
        else:
            print(f"Web search for '{query}' found no organic results.")
            return "No relevant information found on the web."
            
        return "\n".join(results_text)
        
    except requests.exceptions.RequestException as e:
        print(f"Web search failed: {e}")
        return f"An error occurred during web search: {e}"

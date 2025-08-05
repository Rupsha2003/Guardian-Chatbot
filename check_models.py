import google.generativeai as genai
from config.api_keys import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

print("Listing available models...")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"Model: {model.name}")

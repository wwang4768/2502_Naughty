# utils/gemini_setup.py
import google.generativeai as genai
import os
from pathlib import Path
from dotenv import load_dotenv

def setup_gemini():
    """
    Setup and test Gemini API access
    """
    load_dotenv()
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file")
    
    genai.configure(api_key=api_key)
    
    # Test the configuration
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Hello, this is a test.")
        print("Gemini API test successful!")
        return True
    except Exception as e:
        print(f"Gemini API test failed: {str(e)}")
        return False

if __name__ == "__main__":
    setup_gemini()
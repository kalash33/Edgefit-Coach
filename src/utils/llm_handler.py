"""
Simple LLM Handler - Import and use anywhere!
Usage: from llm_handler import ask_llm
       response = ask_llm("Your question here")
"""

import requests
import yaml
import os
import logging

# Import translation support
try:
    from .sarvam_translator import get_translator, translate_text
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    logging.warning("⚠️ Translation module not available")

# Try to import Sarvam Imagine SDK
try:
    from imagine import ChatMessage, ImagineClient
    SARVAM_SDK_AVAILABLE = True
    print("✅ Sarvam Imagine SDK available")
except ImportError:
    SARVAM_SDK_AVAILABLE = False
    print("⚠️ Sarvam Imagine SDK not available, using fallback API")

def ask_llm(prompt, target_language=None):
    """
    Ask the LLM a question and get a response in the specified language
    
    Args:
        prompt (str): Your question or prompt for the LLM
        target_language (str, optional): Target language code (e.g., 'hi', 'ta', 'te')
        
    Returns:
        str: The LLM's response, or an error message if something went wrong
        
    Example:
        response = ask_llm("What is good posture?", target_language="hi")
        if not response.startswith("❌"):
            print(f"LLM says: {response}")
    """
    
    # Try Sarvam Imagine SDK first (the working one)
    if SARVAM_SDK_AVAILABLE:
        try:
            print("🚀 Using Sarvam Imagine SDK...")
            
            # Initialize Sarvam client
            client = ImagineClient(
                api_key="f66499e9-2d54-4adf-85c1-5c9d67a13b1b",
                endpoint="http://10.190.147.82:5050/v2"
            )
            
            # Add language-specific instruction if target language is specified
            enhanced_prompt = prompt
            if target_language and target_language != "en":
                # Map language codes to language names for better LLM understanding
                language_names = {
                    "hi": "Hindi (हिंदी)",
                    "ta": "Tamil (தமிழ்)",
                    "te": "Telugu (తెలుగు)",
                    "bn": "Bengali (বাংলা)",
                    "gu": "Gujarati (ગુજરાતી)",
                    "mr": "Marathi (मराठी)",
                    "kn": "Kannada (ಕನ್ನಡ)"
                }
                
                language_name = language_names.get(target_language, target_language)
                enhanced_prompt = f"{prompt}\n\nIMPORTANT: Please respond ONLY in {language_name} language. Do not use English at all. Write your entire response in {language_name} script and language."
            
            # Make request using Sarvam SDK
            response = client.chat(
                messages=[ChatMessage(role="user", content=enhanced_prompt)],
                model="Sarvam-m"
            )
            
            llm_response = response.first_content
            print(f"✅ Sarvam SDK response received: {llm_response[:100]}...")
            return llm_response
            
        except Exception as e:
            print(f"❌ Sarvam SDK error: {e}")
            # Fall back to original API
    
    # Fallback to original API (if Sarvam SDK fails)
    print("🔄 Falling back to original API...")
    
    # Find config.yaml in project structure
    config_path = None
    
    # Get project root directory (go up from src/utils to project root)
    current_dir = os.path.dirname(os.path.abspath(__file__))  # src/utils
    project_root = os.path.dirname(os.path.dirname(current_dir))  # project root
    
    # Check for config.yaml in config/ directory
    config_locations = [
        os.path.join(project_root, 'config', 'config.yaml'),  # config/config.yaml
        os.path.join(project_root, 'config.yaml'),            # config.yaml (fallback)
        os.path.join(os.getcwd(), 'config', 'config.yaml'),   # current dir/config/config.yaml
        os.path.join(os.getcwd(), 'config.yaml')              # current dir/config.yaml
    ]
    
    for test_path in config_locations:
        if os.path.exists(test_path):
            config_path = test_path
            break
    
    if not config_path:
        return "❌ config.yaml not found"
    
    try:
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Add language-specific instruction if target language is specified
        enhanced_prompt = prompt
        if target_language and target_language != "en":
            # Map language codes to language names for better LLM understanding
            language_names = {
                "hi": "Hindi (हिंदी)",
                "ta": "Tamil (தமிழ்)",
                "te": "Telugu (తెలుగు)",
                "bn": "Bengali (বাংলা)",
                "gu": "Gujarati (ગુજરાતી)",
                "mr": "Marathi (मराठी)",
                "kn": "Kannada (ಕನ್ನಡ)"
            }
            
            language_name = language_names.get(target_language, target_language)
            enhanced_prompt = f"{prompt}\n\nIMPORTANT: Please respond ONLY in {language_name} language. Do not use English at all. Write your entire response in {language_name} script and language."
        
        # Make API request
        url = f"{config['model_server_base_url']}/workspace/{config['workspace_slug']}/chat"
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        payload = {
            "message": enhanced_prompt,
            "mode": "chat", 
            "sessionId": "handler-session",
            "attachments": []
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            llm_response = response.json().get('textResponse', '❌ No response received')
            return llm_response
        else:
            return f"❌ API Error: {response.status_code}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

def is_error_response(response):
    """
    Check if the response is an error message
    
    Args:
        response (str): The response from ask_llm()
        
    Returns:
        bool: True if it's an error, False if it's a valid response
    """
    return response.startswith("❌") 
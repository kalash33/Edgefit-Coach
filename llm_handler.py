"""
Simple LLM Handler - Import and use anywhere!
Usage: from llm_handler import ask_llm
       response = ask_llm("Your question here")
"""

import requests
import yaml
import os

def ask_llm(prompt):
    """
    Ask the LLM a question and get a response
    
    Args:
        prompt (str): Your question or prompt for the LLM
        
    Returns:
        str: The LLM's response, or an error message if something went wrong
        
    Example:
        response = ask_llm("What is good posture?")
        if not response.startswith("❌"):
            print(f"LLM says: {response}")
    """
    # Find config.yaml in current or parent directories
    config_path = None
    current_dir = os.getcwd()
    
    # Check current directory and up to 3 parent directories
    for _ in range(4):
        test_path = os.path.join(current_dir, 'config.yaml')
        if os.path.exists(test_path):
            config_path = test_path
            break
        current_dir = os.path.dirname(current_dir)
    
    if not config_path:
        return "❌ config.yaml not found"
    
    try:
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Make API request
        url = f"{config['model_server_base_url']}/workspace/{config['workspace_slug']}/chat"
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        payload = {
            "message": prompt,
            "mode": "chat", 
            "sessionId": "handler-session",
            "attachments": []
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json().get('textResponse', '❌ No response received')
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
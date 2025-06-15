#!/usr/bin/env python3
"""
Local Sarvam Model Handler for Edgefit-Coach
===========================================

This script provides local Sarvam model integration for multilingual support
in the Edgefit-Coach application. It handles translation and language-specific
AI responses using the Sarvam Local Model.

Usage:
    python local_sarvam.py --text "Hello" --target-lang hi
    python local_sarvam.py --interactive
"""

import argparse
import sys
import os
import json
from typing import Dict, Optional

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def initialize_sarvam():
    """Initialize Sarvam SDK."""
    try:
        from imagine_sdk import ImagineClient
        client = ImagineClient()
        print("✅ Sarvam SDK initialized successfully")
        return client
    except ImportError:
        print("❌ Sarvam SDK not found. Please install using:")
        print("   pip install imagine_sdk-0.4.2-py3-none-any.whl")
        return None
    except Exception as e:
        print(f"❌ Error initializing Sarvam SDK: {e}")
        return None

def translate_text(client, text: str, source_lang: str = "en", target_lang: str = "hi") -> str:
    """Translate text using Sarvam model."""
    if not client:
        return text
    
    try:
        response = client.translate(
            text=text,
            source_language=source_lang,
            target_language=target_lang
        )
        return response.get("translated_text", text)
    except Exception as e:
        print(f"❌ Translation error: {e}")
        return text

def generate_multilingual_response(client, prompt: str, target_lang: str = "hi") -> str:
    """Generate AI response in target language."""
    if not client:
        return "Sarvam client not available"
    
    try:
        # First generate response in English
        english_response = client.generate(
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )
        
        # Then translate to target language if not English
        if target_lang != "en":
            return translate_text(client, english_response, "en", target_lang)
        else:
            return english_response
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return "Error generating response"

def interactive_mode():
    """Run interactive translation mode."""
    client = initialize_sarvam()
    if not client:
        return
    
    print("\n🌐 Sarvam Interactive Translation Mode")
    print("=" * 50)
    print("Supported languages: en, hi, ta, te, bn, gu, mr, kn")
    print("Commands: 'quit' to exit, 'lang <code>' to change target language")
    print("=" * 50)
    
    target_lang = "hi"  # Default to Hindi
    
    while True:
        try:
            user_input = input(f"\n[{target_lang}] Enter text to translate: ").strip()
            
            if user_input.lower() == 'quit':
                print("👋 Goodbye!")
                break
            
            if user_input.startswith('lang '):
                new_lang = user_input.split(' ', 1)[1].strip()
                if new_lang in ['en', 'hi', 'ta', 'te', 'bn', 'gu', 'mr', 'kn']:
                    target_lang = new_lang
                    print(f"🌐 Target language changed to: {target_lang}")
                else:
                    print("❌ Unsupported language. Use: en, hi, ta, te, bn, gu, mr, kn")
                continue
            
            if user_input:
                translated = translate_text(client, user_input, "en", target_lang)
                print(f"📝 Original: {user_input}")
                print(f"🌐 Translated ({target_lang}): {translated}")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Sarvam Local Model Handler")
    parser.add_argument("--text", help="Text to translate")
    parser.add_argument("--source-lang", default="en", help="Source language (default: en)")
    parser.add_argument("--target-lang", default="hi", help="Target language (default: hi)")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--test", action="store_true", help="Run test translations")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
        return
    
    # Initialize Sarvam client
    client = initialize_sarvam()
    if not client:
        sys.exit(1)
    
    if args.test:
        # Test translations
        test_texts = [
            "Hello, how are you?",
            "Good posture is important for health",
            "Please sit up straight",
            "Your posture is excellent today!"
        ]
        
        print("\n🧪 Testing Sarvam Translations")
        print("=" * 50)
        
        for text in test_texts:
            print(f"\n📝 Original: {text}")
            for lang in ['hi', 'ta', 'te']:
                translated = translate_text(client, text, "en", lang)
                print(f"🌐 {lang}: {translated}")
        
        return
    
    if args.text:
        # Single translation
        translated = translate_text(client, args.text, args.source_lang, args.target_lang)
        print(f"📝 Original ({args.source_lang}): {args.text}")
        print(f"🌐 Translated ({args.target_lang}): {translated}")
    else:
        print("❌ Please provide --text, --interactive, or --test option")
        parser.print_help()

if __name__ == "__main__":
    main()
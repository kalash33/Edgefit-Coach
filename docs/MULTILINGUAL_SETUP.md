# 🌐 Multilingual Support Setup Guide

## Overview

Edgefit-Coach now supports multiple Indian languages using the Sarvam Local Model. This feature allows users to interact with the AI coach in their preferred language and receive responses in the same language.

## Supported Languages

- 🇺🇸 **English** (en) - Default
- 🇮🇳 **Hindi** (hi) - हिंदी
- 🇮🇳 **Tamil** (ta) - தமிழ்
- 🇮🇳 **Telugu** (te) - తెలుగు
- 🇮🇳 **Bengali** (bn) - বাংলা
- 🇮🇳 **Gujarati** (gu) - ગુજરાતી
- 🇮🇳 **Marathi** (mr) - मराठी
- 🇮🇳 **Kannada** (kn) - ಕನ್ನಡ

## Prerequisites

### 1. WiFi Connection
**IMPORTANT**: You MUST be connected to the event WiFi to access the Sarvam model.

1. Connect to **"Workshop[number]_5G"** network
2. Enter the provided credentials
3. Ensure internet access is available

### 2. Sarvam SDK Installation

```bash
# Create virtual environment (if not already done)
python -m venv venv
.\venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install Sarvam SDK wheel file
pip install imagine_sdk-0.4.2-py3-none-any.whl

# Install optional dependencies
pip install prettyprinter  # For pretty printing (optional)
```

## Setup Instructions

### Step 1: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Install Sarvam SDK (manual installation required)
pip install imagine_sdk-0.4.2-py3-none-any.whl
```

### Step 2: Test Sarvam Connection

```bash
# Test the Sarvam SDK installation
python local_sarvam.py --test

# Interactive translation mode
python local_sarvam.py --interactive

# Single translation test
python local_sarvam.py --text "Hello, how are you?" --target-lang hi
```

### Step 3: Launch Application

```bash
# Start the complete web application with multilingual support
python edgefit_coach.py web
```

## Features

### 1. Language Selection
- **Location**: Bottom left of navigation menu in Streamlit frontend
- **Options**: Dropdown with flag icons and native language names
- **Persistence**: Language preference maintained during session

### 2. UI Translation
- **Static Elements**: All menu items, buttons, and labels translated
- **Dynamic Content**: Real-time translation of AI responses
- **Fallback**: English used if translation fails

### 3. AI Chat in Multiple Languages
- **Input**: Type in English (using English keyboard)
- **Output**: AI responses in selected language
- **Context**: Conversation history maintained with language metadata

### 4. Posture Notifications
- **Desktop Notifications**: Translated to selected language
- **AI Quotes**: Motivation messages in user's preferred language
- **Status Messages**: System status in selected language

## Usage Examples

### Language Selection
1. Open Streamlit frontend (`http://localhost:8501`)
2. Look for "🌐 Language Settings" in the sidebar
3. Select your preferred language from dropdown
4. Interface will refresh with translations

### Multilingual Chat
1. Select your language (e.g., Hindi)
2. Go to Chat Interface
3. Type your message in English: "What is good posture?"
4. Receive response in Hindi: "अच्छी मुद्रा क्या है..."

### Testing Translations
```bash
# Test Hindi translation
python local_sarvam.py --text "Good posture is important" --target-lang hi

# Test Tamil translation
python local_sarvam.py --text "Sit up straight" --target-lang ta

# Interactive mode for multiple tests
python local_sarvam.py --interactive
```

## Technical Architecture

### Translation Flow
1. **UI Elements**: Static translations from `UI_TRANSLATIONS` dictionary
2. **Dynamic Content**: Sarvam API for real-time translation
3. **AI Responses**: Enhanced prompts + post-translation
4. **Fallback**: English used if Sarvam unavailable

### File Structure
```
src/utils/sarvam_translator.py    # Translation handler
local_sarvam.py                   # Standalone Sarvam client
src/frontend/frontend_test.py     # UI with language selection
src/api/api_server.py            # Multilingual API endpoints
```

### API Integration
- **Chat Endpoint**: `/chat/message` accepts `target_language` parameter
- **Response Format**: Includes language metadata
- **Error Handling**: Graceful fallback to English

## Troubleshooting

### Common Issues

#### 1. Sarvam SDK Not Found
```bash
# Error: ModuleNotFoundError: No module named 'imagine_sdk'
# Solution: Install the wheel file
pip install imagine_sdk-0.4.2-py3-none-any.whl
```

#### 2. Network Connection Issues
```bash
# Error: Connection timeout
# Solution: Ensure you're on the event WiFi
# Check: Workshop[number]_5G network connection
```

#### 3. Translation Not Working
```bash
# Check if Sarvam is available
python -c "from src.utils.sarvam_translator import get_translator; print(get_translator().sarvam_available)"

# Test direct translation
python local_sarvam.py --text "test" --target-lang hi
```

#### 4. UI Not Translating
- Refresh the page after language selection
- Check browser console for JavaScript errors
- Verify translation module import in frontend

### Debug Mode

```bash
# Enable debug logging
export EDGEFIT_LOG_LEVEL=DEBUG

# Test translation module
python -c "
import sys
sys.path.append('src')
from utils.sarvam_translator import get_translator, t
translator = get_translator()
print('Current language:', translator.get_current_language())
print('Test translation:', t('app_title'))
"
```

## Performance Considerations

### Translation Caching
- Static UI translations cached in memory
- Dynamic translations not cached (real-time)
- Consider implementing cache for frequently used phrases

### Network Usage
- Each dynamic translation requires API call
- Minimize translations for better performance
- Use static translations for UI elements

### Fallback Strategy
- English used if Sarvam unavailable
- Graceful degradation without breaking functionality
- User notified of translation limitations

## Development

### Adding New Languages
1. Add language to `SUPPORTED_LANGUAGES` in `sarvam_translator.py`
2. Add UI translations to `UI_TRANSLATIONS` dictionary
3. Test with Sarvam API for dynamic content

### Adding New UI Elements
1. Add English text to `UI_TRANSLATIONS["en"]`
2. Add translations for all supported languages
3. Use `t("key")` function in frontend code

### Custom Translation Logic
```python
from utils.sarvam_translator import get_translator, translate_text

# Get current language
translator = get_translator()
current_lang = translator.get_current_language()

# Translate specific text
translated = translate_text("Your text here", target_lang)
```

## Security Considerations

- Sarvam API calls made over HTTPS
- No sensitive data sent for translation
- User language preference not stored permanently
- Network traffic encrypted

## Future Enhancements

1. **Voice Input**: Speech-to-text in multiple languages
2. **Voice Output**: Text-to-speech responses
3. **Regional Variants**: Support for regional language variants
4. **Offline Mode**: Local translation models
5. **Translation Cache**: Improve performance with caching

## Support

For issues with multilingual support:

1. Check network connection to event WiFi
2. Verify Sarvam SDK installation
3. Test with `local_sarvam.py` script
4. Check application logs for translation errors
5. Report issues with language code and error message

---

**Made with 🌐 by the Edgefit-Coach Team** 
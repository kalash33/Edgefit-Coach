"""
Sarvam Translation Handler for Multilingual Support
==================================================

This module provides translation capabilities using the Sarvam Local Model
for supporting multiple Indian languages in the Edgefit-Coach application.

Supported Languages:
- English (en)
- Hindi (hi) 
- Tamil (ta)
- Telugu (te)
- Bengali (bn)
- Gujarati (gu)
- Marathi (mr)
- Kannada (kn)
"""

import os
import json
from typing import Dict, Optional, List
import logging

# Language configuration
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "flag": "🇺🇸", "code": "en"},
    "hi": {"name": "हिंदी", "flag": "🇮🇳", "code": "hi"},
    "ta": {"name": "தமிழ்", "flag": "🇮🇳", "code": "ta"},
    "te": {"name": "తెలుగు", "flag": "🇮🇳", "code": "te"},
    "bn": {"name": "বাংলা", "flag": "🇮🇳", "code": "bn"},
    "gu": {"name": "ગુજરાતી", "flag": "🇮🇳", "code": "gu"},
    "mr": {"name": "मराठी", "flag": "🇮🇳", "code": "mr"},
    "kn": {"name": "ಕನ್ನಡ", "flag": "🇮🇳", "code": "kn"}
}

# Static translations for UI elements
UI_TRANSLATIONS = {
    "en": {
        "app_title": "Edgefit Coach - AI Posture and Fitness Assistant",
        "navigation": "Navigation",
        "choose_section": "Choose a section:",
        "language_settings": "Language Settings",
        "select_language": "Select Language:",
        "live_video": "Live Video & Motivation",
        "dashboard": "Dashboard Data", 
        "chat_interface": "Chat Interface",
        "analysis_reports": "Analysis & Reports",
        "system_status": "System Status",
        "video_stream_control": "Video Stream Control",
        "live_video_stream": "Live Video Stream",
        "ai_coach_feed": "Live AI Coach Feed",
        "connecting": "Connecting to AI Coach...",
        "connection_lost": "Connection Lost",
        "attempting_reconnect": "Attempting to reconnect in 3 seconds...",
        "ai_coach_stats": "AI Coach Statistics:",
        "good_posture": "Good Posture",
        "slouching": "Slouching",
        "posture_percentage": "Posture Percentage",
        "start_video": "Start Video",
        "stop_video": "Stop Video",
        "video_status": "Video Status",
        "send_message": "Send Message",
        "chat_history": "Chat History",
        "clear_history": "Clear History",
        "generate_report": "Generate Report",
        "download_report": "Download Report",
        "system_health": "System Health",
        "api_status": "API Status",
        "websocket_status": "WebSocket Status",
        "ai_coach_connected": "AI Coach Connected - LIVE",
        "ai_coach_says": "AI COACH SAYS:",
        "stream_status_running": "Stream Status: RUNNING",
        "restart_stream": "Restart Stream",
        "stop_stream": "Stop Stream",
        "live_pose_detection": "LIVE - Pose Detection Active",
        "ai_coach_statistics": "AI Coach Statistics:",
        "total_quotes": "Total Quotes",
        "avg_performance": "Avg Performance",
        "total_readings": "Total Readings",
        "latest_ai_quote": "Latest AI quote:",
        "no_ai_coaching_data": "No AI coaching data available yet.",
        "start_video_streaming": "Start video streaming to generate AI coaching quotes.",
        "good": "Good",
        "slouch": "Slouch",
        "performance": "Performance"
    },
    "hi": {
        "app_title": "एजफिट कोच - एआई पोस्चर और फिटनेस सहायक",
        "navigation": "नेविगेशन",
        "choose_section": "एक सेक्शन चुनें:",
        "language_settings": "भाषा सेटिंग्स",
        "select_language": "भाषा चुनें:",
        "live_video": "लाइव वीडियो और प्रेरणा",
        "dashboard": "डैशबोर्ड डेटा",
        "chat_interface": "चैट इंटरफेस",
        "analysis_reports": "विश्लेषण और रिपोर्ट",
        "system_status": "सिस्टम स्थिति",
        "video_stream_control": "वीडियो स्ट्रीम नियंत्रण",
        "live_video_stream": "लाइव वीडियो स्ट्रीम",
        "ai_coach_feed": "लाइव एआई कोच फीड",
        "connecting": "एआई कोच से कनेक्ट हो रहे हैं...",
        "connection_lost": "कनेक्शन खो गया",
        "attempting_reconnect": "3 सेकंड में फिर से कनेक्ट करने की कोशिश कर रहे हैं...",
        "ai_coach_stats": "एआई कोच आंकड़े:",
        "good_posture": "अच्छी मुद्रा",
        "slouching": "झुकना",
        "posture_percentage": "मुद्रा प्रतिशत",
        "start_video": "वीडियो शुरू करें",
        "stop_video": "वीडियो बंद करें",
        "video_status": "वीडियो स्थिति",
        "send_message": "संदेश भेजें",
        "chat_history": "चैट इतिहास",
        "clear_history": "इतिहास साफ़ करें",
        "generate_report": "रिपोर्ट बनाएं",
        "download_report": "रिपोर्ट डाउनलोड करें",
        "system_health": "सिस्टम स्वास्थ्य",
        "api_status": "एपीआई स्थिति",
        "websocket_status": "वेबसॉकेट स्थिति",
        "ai_coach_connected": "एआई कोच कनेक्टेड - लाइव",
        "ai_coach_says": "एआई कोच कहता है:",
        "stream_status_running": "स्ट्रीम स्थिति: चल रहा है",
        "restart_stream": "स्ट्रीम पुनः आरंभ करें",
        "stop_stream": "स्ट्रीम बंद करें",
        "live_pose_detection": "लाइव - पोज़ डिटेक्शन सक्रिय",
        "ai_coach_statistics": "एआई कोच आंकड़े:",
        "total_quotes": "कुल उद्धरण",
        "avg_performance": "औसत प्रदर्शन",
        "total_readings": "कुल रीडिंग",
        "latest_ai_quote": "नवीनतम एआई उद्धरण:",
        "no_ai_coaching_data": "अभी तक कोई एआई कोचिंग डेटा उपलब्ध नहीं है।",
        "start_video_streaming": "एआई कोचिंग उद्धरण उत्पन्न करने के लिए वीडियो स्ट्रीमिंग शुरू करें।",
        "good": "अच्छा",
        "slouch": "झुकना",
        "performance": "प्रदर्शन"
    },
    "ta": {
        "app_title": "எட்ஜ்ஃபிட் கோச் - AI தோற்றம் மற்றும் உடற்பயிற்சி உதவியாளர்",
        "navigation": "வழிசெலுத்தல்",
        "choose_section": "ஒரு பிரிவைத் தேர்ந்தெடுக்கவும்:",
        "language_settings": "மொழி அமைப்புகள்",
        "select_language": "மொழியைத் தேர்ந்தெடுக்கவும்:",
        "live_video": "நேரடி வீடியோ மற்றும் உத்வேகம்",
        "dashboard": "டாஷ்போர்டு தரவு",
        "chat_interface": "அரட்டை இடைமுகம்",
        "analysis_reports": "பகுப்பாய்வு மற்றும் அறிக்கைகள்",
        "system_status": "கணினி நிலை",
        "video_stream_control": "வீடியோ ஸ்ட்ரீம் கட்டுப்பாடு",
        "live_video_stream": "நேரடி வீடியோ ஸ்ட்ரீம்",
        "ai_coach_feed": "நேரடி AI பயிற்சியாளர் ஊட்டம்",
        "connecting": "AI பயிற்சியாளருடன் இணைக்கிறது...",
        "connection_lost": "இணைப்பு இழந்தது",
        "attempting_reconnect": "3 வினாடிகளில் மீண்டும் இணைக்க முயற்சிக்கிறது...",
        "ai_coach_stats": "AI பயிற்சியாளர் புள்ளிவிவரங்கள்:",
        "good_posture": "நல்ல தோற்றம்",
        "slouching": "சாய்தல்",
        "posture_percentage": "தோற்ற சதவீதம்",
        "start_video": "வீடியோ தொடங்கு",
        "stop_video": "வீடியோ நிறுத்து",
        "video_status": "வீடியோ நிலை",
        "send_message": "செய்தி அனுப்பு",
        "chat_history": "அரட்டை வரலாறு",
        "clear_history": "வரலாற்றை அழி",
        "generate_report": "அறிக்கை உருவாக்கு",
        "download_report": "அறிக்கை பதிவிறக்கு",
        "system_health": "கணினி ஆரோக்கியம்",
        "api_status": "API நிலை",
        "websocket_status": "வெப்சாக்கெட் நிலை",
        "ai_coach_connected": "AI பயிற்சியாளர் இணைக்கப்பட்டது - நேரடி",
        "ai_coach_says": "AI பயிற்சியாளர் கூறுகிறார்:",
        "stream_status_running": "ஸ்ட்ரீம் நிலை: இயங்குகிறது",
        "restart_stream": "ஸ்ட்ரீம் மீண்டும் தொடங்கு",
        "stop_stream": "ஸ்ட்ரீம் நிறுத்து",
        "live_pose_detection": "நேரடி - போஸ் கண்டறிதல் செயலில்",
        "ai_coach_statistics": "AI பயிற்சியாளர் புள்ளிவிவரங்கள்:",
        "total_quotes": "மொத்த மேற்கோள்கள்",
        "avg_performance": "சராசரி செயல்திறன்",
        "total_readings": "மொத்த வாசிப்புகள்",
        "latest_ai_quote": "சமீபத்திய AI மேற்கோள்:",
        "no_ai_coaching_data": "இன்னும் AI பயிற்சி தரவு எதுவும் கிடைக்கவில்லை।",
        "start_video_streaming": "AI பயிற்சி மேற்கோள்களை உருவாக்க வீடியோ ஸ்ட்ரீமிங் தொடங்கவும்।",
        "good": "நல்லது",
        "slouch": "சாய்வு",
        "performance": "செயல்திறன்"
    },
    "te": {
        "app_title": "ఎడ్జ్‌ఫిట్ కోచ్ - AI భంగిమ మరియు ఫిట్‌నెస్ సహాయకుడు",
        "navigation": "నావిగేషన్",
        "choose_section": "ఒక విభాగాన్ని ఎంచుకోండి:",
        "language_settings": "భాష సెట్టింగులు",
        "select_language": "భాషను ఎంచుకోండి:",
        "live_video": "లైవ్ వీడియో మరియు ప్రేరణ",
        "dashboard": "డాష్‌బోర్డ్ డేటా",
        "chat_interface": "చాట్ ఇంటర్‌ఫేస్",
        "analysis_reports": "విశ్లేషణ మరియు నివేదికలు",
        "system_status": "సిస్టమ్ స్థితి",
        "video_stream_control": "వీడియో స్ట్రీమ్ నియంత్రణ",
        "live_video_stream": "లైవ్ వీడియో స్ట్రీమ్",
        "ai_coach_feed": "లైవ్ AI కోచ్ ఫీడ్",
        "connecting": "AI కోచ్‌కు కనెక్ట్ అవుతోంది...",
        "connection_lost": "కనెక్షన్ కోల్పోయింది",
        "attempting_reconnect": "3 సెకన్లలో మళ్లీ కనెక్ట్ చేయడానికి ప్రయత్నిస్తోంది...",
        "ai_coach_stats": "AI కోచ్ గణాంకాలు:",
        "good_posture": "మంచి భంగిమ",
        "slouching": "వంగడం",
        "posture_percentage": "భంగిమ శాతం",
        "start_video": "వీడియో ప్రారంభించు",
        "stop_video": "వీడియో ఆపు",
        "video_status": "వీడియో స్థితి",
        "send_message": "సందేశం పంపు",
        "chat_history": "చాట్ చరిత్ర",
        "clear_history": "చరిత్రను క్లియర్ చేయి",
        "generate_report": "నివేదిక రూపొందించు",
        "download_report": "నివేదిక డౌన్‌లోడ్ చేయి",
        "system_health": "సిస్టమ్ ఆరోగ్యం",
        "api_status": "API స్థితి",
        "websocket_status": "వెబ్‌సాకెట్ స్థితి",
        "ai_coach_connected": "AI కోచ్ కనెక్ట్ అయ్యింది - లైవ్",
        "ai_coach_says": "AI కోచ్ చెబుతోంది:",
        "stream_status_running": "స్ట్రీమ్ స్థితి: రన్ అవుతోంది",
        "restart_stream": "స్ట్రీమ్ మళ్లీ ప్రారంభించు",
        "stop_stream": "స్ట్రీమ్ ఆపు",
        "live_pose_detection": "లైవ్ - పోజ్ డిటెక్షన్ యాక్టివ్",
        "ai_coach_statistics": "AI కోచ్ గణాంకాలు:",
        "total_quotes": "మొత్తం కోట్స్",
        "avg_performance": "సగటు పనితీరు",
        "total_readings": "మొత్తం రీడింగ్‌లు",
        "latest_ai_quote": "తాజా AI కోట్:",
        "no_ai_coaching_data": "ఇంకా AI కోచింగ్ డేటా అందుబాటులో లేదు।",
        "start_video_streaming": "AI కోచింగ్ కోట్స్ జనరేట్ చేయడానికి వీడియో స్ట్రీమింగ్ ప్రారంభించండి।",
        "good": "మంచిది",
        "slouch": "వంగడం",
        "performance": "పనితీరు"
    }
}

class SarvamTranslator:
    """Sarvam-based translation handler for multilingual support."""
    
    def __init__(self):
        """Initialize the Sarvam translator."""
        self.current_language = "en"  # Default to English
        self.sarvam_available = False
        self.language_state_file = os.path.join(os.path.dirname(__file__), "..", "..", "temp", "language_state.json")
        self._load_language_state()
        self._initialize_sarvam()
    
    def _load_language_state(self):
        """Load the current language from state file"""
        try:
            if os.path.exists(self.language_state_file):
                with open(self.language_state_file, 'r') as f:
                    data = json.load(f)
                    self.current_language = data.get('current_language', 'en')
        except Exception as e:
            print(f"Warning: Could not load language state: {e}")
            self.current_language = "en"
    
    def _save_language_state(self):
        """Save the current language to state file"""
        try:
            os.makedirs(os.path.dirname(self.language_state_file), exist_ok=True)
            with open(self.language_state_file, 'w') as f:
                json.dump({'current_language': self.current_language}, f)
        except Exception as e:
            print(f"Warning: Could not save language state: {e}")
    
    def _initialize_sarvam(self):
        """Initialize Sarvam SDK if available."""
        try:
            # Try to import Sarvam SDK
            from imagine_sdk import ImagineClient
            self.sarvam_client = ImagineClient()
            self.sarvam_available = True
            logging.info("✅ Sarvam SDK initialized successfully")
        except ImportError:
            logging.warning("⚠️ Sarvam SDK not available, using static translations only")
            self.sarvam_available = False
        except Exception as e:
            logging.error(f"❌ Error initializing Sarvam SDK: {e}")
            self.sarvam_available = False
    
    def set_language(self, language_code: str) -> bool:
        """Set the current language and persist it."""
        if language_code in SUPPORTED_LANGUAGES:
            self.current_language = language_code
            self._save_language_state()
            logging.info(f"🌐 Language set to: {SUPPORTED_LANGUAGES[language_code]['name']}")
            return True
        return False
    
    def get_current_language(self) -> str:
        """Get the current language code."""
        return self.current_language
    
    def get_supported_languages(self) -> Dict:
        """Get all supported languages."""
        return SUPPORTED_LANGUAGES
    
    def translate_ui_text(self, key: str) -> str:
        """Translate UI text using static translations."""
        if self.current_language in UI_TRANSLATIONS:
            return UI_TRANSLATIONS[self.current_language].get(key, key)
        return key
    
    def translate_dynamic_text(self, text: str, target_language: str = None) -> str:
        """Translate dynamic text using Sarvam API."""
        if target_language is None:
            target_language = self.current_language
        
        # If target is English or Sarvam not available, return original
        if target_language == "en" or not self.sarvam_available:
            return text
        
        try:
            # Use Sarvam for translation
            response = self.sarvam_client.translate(
                text=text,
                source_language="en",
                target_language=target_language
            )
            return response.get("translated_text", text)
        except Exception as e:
            logging.error(f"❌ Translation error: {e}")
            return text
    
    def translate_ai_response(self, response: str) -> str:
        """Translate AI coach responses to current language."""
        return self.translate_dynamic_text(response, self.current_language)
    
    def get_language_prompt_suffix(self) -> str:
        """Get language-specific prompt suffix for AI responses."""
        if self.current_language == "en":
            return ""
        
        language_name = SUPPORTED_LANGUAGES[self.current_language]["name"]
        return f" Please respond in {language_name} language."

# Global translator instance
translator = SarvamTranslator()

def get_translator() -> SarvamTranslator:
    """Get the global translator instance."""
    return translator

def t(key: str) -> str:
    """Quick translation function for UI text."""
    return translator.translate_ui_text(key)

def translate_text(text: str, target_language: str = None) -> str:
    """Quick translation function for dynamic text."""
    return translator.translate_dynamic_text(text, target_language) 
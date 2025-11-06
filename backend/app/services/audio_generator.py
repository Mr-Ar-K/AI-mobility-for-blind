"""
Audio Generation Service
Converts detection text alerts into speech audio using gTTS and pydub
"""

from gtts import gTTS
from pydub import AudioSegment
import re
import os
import tempfile
from typing import List
from pathlib import Path
import uuid

class AudioGenerator:
    """
    Generates audio warnings from detection text messages.
    Uses Google Text-to-Speech (gTTS) for voice generation.
    """
    
    def __init__(self, language='en', pause_duration=600):
        """
        Initialize the audio generator.
        
        Args:
            language (str): Language code for TTS (default: 'en')
            pause_duration (int): Pause duration between sentences in milliseconds (default: 600ms)
        """
        self.language = language
        self.pause_duration = pause_duration
    
    def clean_text(self, text: str) -> str:
        """
        Clean and simplify detection text for better TTS output.
        Translates to Telugu or Hindi based on language setting.
        
        Args:
            text (str): Raw detection text with frame numbers and confidence scores
            
        Returns:
            str: Cleaned and translated text suitable for TTS
        """
        # Remove confidence scores
        clean = re.sub(r"\(conf: [0-9.]+\)", "", text)
        
        # Remove frame numbers
        clean = re.sub(r"\[Frame \d+\]\s*", "", clean)
        
        # Language-specific replacements
        if self.language == 'te':  # Telugu
            # First, handle dynamic numbers in complete sentences using regex patterns
            clean = re.sub(r"Watch out! (\d+) cars right in front of you! Stay where you are!", 
                          r"జాగ్రత్త! మీ ముందే \1 కార్లు ఉన్నాయి! అక్కడే ఉండండి!", clean)
            clean = re.sub(r"Careful! (\d+) cars coming towards you\.", 
                          r"జాగ్రత్త! మీ వైపు \1 కార్లు వస్తున్నాయి.", clean)
            clean = re.sub(r"Warning! (\d+) cars on your left side! Don't move!", 
                          r"హెచ్చరిక! మీ ఎడమవైపు \1 కార్లు ఉన్నాయి! కదలవద్దు!", clean)
            clean = re.sub(r"(\d+) cars approaching on your left\.", 
                          r"మీ ఎడమవైపు \1 కార్లు వస్తున్నాయి.", clean)
            clean = re.sub(r"Warning! (\d+) cars on your right side! Don't move!", 
                          r"హెచ్చరిక! మీ కుడివైపు \1 కార్లు ఉన్నాయి! కదలవద్దు!", clean)
            clean = re.sub(r"(\d+) cars approaching on your right\.", 
                          r"మీ కుడివైపు \1 కార్లు వస్తున్నాయి.", clean)
            clean = re.sub(r"(\d+) people ahead\.", r"ముందు \1 మంది ఉన్నారు.", clean)
            clean = re.sub(r"(\d+) people left\.", r"ఎడమవైపు \1 మంది ఉన్నారు.", clean)
            clean = re.sub(r"(\d+) people right\.", r"కుడివైపు \1 మంది ఉన్నారు.", clean)
            
            replacements = {
                # Complete sentence translations (must come first)
                "Green light ahead. It's safe to cross.": "ముందు ఆకుపచ్చ లైట్. రహదారి దాటడం సురక్షితం.",
                "Zebra crossing in front of you. No vehicles nearby. You can cross now.": "మీ ముందు జీబ్రా క్రాసింగ్ ఉంది. చుట్టూ వాహనాలు లేవు. ఇప్పుడు దాటవచ్చు.",
                "Zebra crossing ahead, but vehicles are nearby. Wait for them to pass.": "ముందు జీబ్రా క్రాసింగ్ ఉంది, కానీ వాహనాలు చుట్టూ ఉన్నాయి. అవి వెళ్ళే వరకు వేచి ఉండండి.",
                "Watch out! A car right in front of you! Stay where you are!": "జాగ్రత్త! మీ ముందే కారు ఉంది! అక్కడే ఉండండి!",
                "Careful! A car coming towards you.": "జాగ్రత్త! మీ వైపు కారు వస్తోంది.",
                "Warning! A car on your left side! Don't move!": "హెచ్చరిక! మీ ఎడమవైపు కారు ఉంది! కదలవద్దు!",
                "A car approaching on your left.": "మీ ఎడమవైపు కారు వస్తోంది.",
                "Warning! A car on your right side! Don't move!": "హెచ్చరిక! మీ కుడివైపు కారు ఉంది! కదలవద్దు!",
                "A car approaching on your right.": "మీ కుడివైపు కారు వస్తోంది.",
                "Person ahead.": "ముందు వ్యక్తి ఉన్నారు.",
                "Person left.": "ఎడమవైపు వ్యక్తి ఉన్నారు.",
                "Person right.": "కుడివైపు వ్యక్తి ఉన్నారు.",
                "No significant detections in this video.": "ఈ వీడియోలో ముఖ్యమైన వస్తువులు కనిపించలేదు.",
                # Word/phrase translations (fallback for any remaining English)
                "Green light": "ఆకుపచ్చ లైట్",
                "Zebra crossing": "జీబ్రా క్రాసింగ్",
                "Person": "వ్యక్తి",
                "people": "మంది",
                "Car": "కారు",
                "cars": "కార్లు",
                "ahead": "ముందు",
                "left": "ఎడమవైపు",
                "right": "కుడివైపు",
                "Watch out": "జాగ్రత్త",
                "Careful": "జాగ్రత్త",
                "Warning": "హెచ్చరిక",
                "Stay where you are": "అక్కడే ఉండండి",
                "Don't move": "కదలవద్దు",
                "Wait": "వేచి ఉండండి",
            }
        elif self.language == 'hi':  # Hindi
            # First, handle dynamic numbers in complete sentences using regex patterns
            clean = re.sub(r"Watch out! (\d+) cars right in front of you! Stay where you are!", 
                          r"सावधान! आपके ठीक सामने \1 कारें हैं! वहीं रुकें!", clean)
            clean = re.sub(r"Careful! (\d+) cars coming towards you\.", 
                          r"सावधान! आपकी ओर \1 कारें आ रही हैं.", clean)
            clean = re.sub(r"Warning! (\d+) cars on your left side! Don't move!", 
                          r"चेतावनी! आपकी बाईं ओर \1 कारें हैं! हिलें नहीं!", clean)
            clean = re.sub(r"(\d+) cars approaching on your left\.", 
                          r"आपकी बाईं ओर \1 कारें आ रही हैं.", clean)
            clean = re.sub(r"Warning! (\d+) cars on your right side! Don't move!", 
                          r"चेतावनी! आपकी दाईं ओर \1 कारें हैं! हिलें नहीं!", clean)
            clean = re.sub(r"(\d+) cars approaching on your right\.", 
                          r"आपकी दाईं ओर \1 कारें आ रही हैं.", clean)
            clean = re.sub(r"(\d+) people ahead\.", r"आगे \1 लोग हैं.", clean)
            clean = re.sub(r"(\d+) people left\.", r"बाईं ओर \1 लोग हैं.", clean)
            clean = re.sub(r"(\d+) people right\.", r"दाईं ओर \1 लोग हैं.", clean)
            
            replacements = {
                # Complete sentence translations (must come first)
                "Green light ahead. It's safe to cross.": "आगे हरी बत्ती है. सड़क पार करना सुरक्षित है.",
                "Zebra crossing in front of you. No vehicles nearby. You can cross now.": "आपके सामने ज़ेबरा क्रॉसिंग है. आसपास कोई वाहन नहीं है. अब आप पार कर सकते हैं.",
                "Zebra crossing ahead, but vehicles are nearby. Wait for them to pass.": "आगे ज़ेबरा क्रॉसिंग है, लेकिन आसपास वाहन हैं. उनके गुज़रने तक प्रतीक्षा करें.",
                "Watch out! A car right in front of you! Stay where you are!": "सावधान! आपके ठीक सामने कार है! वहीं रुकें!",
                "Careful! A car coming towards you.": "सावधान! आपकी ओर कार आ रही है.",
                "Warning! A car on your left side! Don't move!": "चेतावनी! आपकी बाईं ओर कार है! हिलें नहीं!",
                "A car approaching on your left.": "आपकी बाईं ओर कार आ रही है.",
                "Warning! A car on your right side! Don't move!": "चेतावनी! आपकी दाईं ओर कार है! हिलें नहीं!",
                "A car approaching on your right.": "आपकी दाईं ओर कार आ रही है.",
                "Person ahead.": "आगे व्यक्ति है.",
                "Person left.": "बाईं ओर व्यक्ति है.",
                "Person right.": "दाईं ओर व्यक्ति है.",
                "No significant detections in this video.": "इस वीडियो में कोई महत्वपूर्ण वस्तु नहीं मिली.",
                # Word/phrase translations (fallback for any remaining English)
                "Green light": "हरी बत्ती",
                "Zebra crossing": "ज़ेबरा क्रॉसिंग",
                "Person": "व्यक्ति",
                "people": "लोग",
                "Car": "कार",
                "cars": "कारें",
                "ahead": "आगे",
                "left": "बाईं ओर",
                "right": "दाईं ओर",
                "Watch out": "सावधान",
                "Careful": "सावधान",
                "Warning": "चेतावनी",
                "Stay where you are": "वहीं रुकें",
                "Don't move": "हिलें नहीं",
                "Wait": "प्रतीक्षा करें",
            }
        else:  # English (default)
            replacements = {
                # English messages are already natural, just minor cleanup
                # These are mostly for consistency and improving natural flow
                "Green Light": "Green light",
                "zebra crossing": "Zebra crossing",
            }
        
        # Apply replacements (order matters - replace longer phrases first)
        for old, new in sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True):
            clean = clean.replace(old, new)
        
        return clean
    
    def generate_audio_from_alerts(self, alerts: List[str], output_path: str) -> str:
        """
        Generate a single MP3 file from a list of text alerts.
        
        Args:
            alerts (List[str]): List of detection alert messages
            output_path (str): Path where the output MP3 should be saved
            
        Returns:
            str: Path to the generated audio file
        """
        if not alerts:
            # Generate a "no detections" message
            alerts = ["No significant detections in this video."]
        
        # Combine all alerts into one text
        log_text = "\n".join(alerts)
        
        # Clean the text
        clean_text = self.clean_text(log_text)
        
        # Split into sentences (remove empty lines)
        sentences = [s.strip() for s in clean_text.split("\n") if s.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_sentences = []
        for s in sentences:
            if s not in seen:
                seen.add(s)
                unique_sentences.append(s)
        
        # FAST PATH: single TTS request for all sentences to reduce latency
        try:
            # Join sentences with short pauses represented by periods
            # This avoids multiple network calls to gTTS
            joined_text = ". ".join(unique_sentences)
            tts = gTTS(text=joined_text, lang=self.language, slow=False)
            tts.save(output_path)
            return output_path
        except Exception as e:
            # Fallback: try per-sentence merge if single-shot fails
            temp_files = []
            tts_segments = []
            try:
                for i, sentence in enumerate(unique_sentences):
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_tts_{i}.mp3', dir=os.path.dirname(output_path))
                    temp_filename = temp_file.name
                    temp_file.close()
                    tts = gTTS(text=sentence, lang=self.language, slow=False)
                    tts.save(temp_filename)
                    audio_seg = AudioSegment.from_mp3(temp_filename)
                    tts_segments.append(audio_seg)
                    temp_files.append(temp_filename)
                final_audio = AudioSegment.empty()
                for seg in tts_segments:
                    final_audio += seg + AudioSegment.silent(duration=self.pause_duration)
                final_audio.export(output_path, format="mp3")
                for temp_file in temp_files:
                    try: os.remove(temp_file)
                    except: pass
                return output_path
            except Exception as e2:
                for temp_file in temp_files:
                    try: os.remove(temp_file)
                    except: pass
                raise Exception(f"Failed to generate audio (fast and fallback): {str(e2)}")
    
    def generate_audio_quick(self, alerts: List[str]) -> str:
        """
        Generate audio with auto-generated filename in tmp directory.
        
        Args:
            alerts (List[str]): List of detection alert messages
            
        Returns:
            str: Path to the generated audio file
        """
        # Create tmp directory if it doesn't exist
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        filename = f"audio_{uuid.uuid4().hex[:8]}.mp3"
        output_path = tmp_dir / filename
        
        return self.generate_audio_from_alerts(alerts, str(output_path))


# Helper function for easy import
def generate_audio_from_text_list(text_list: List[str], output_path: str = None) -> str:
    """
    Quick helper to generate audio from a list of text strings.
    
    Args:
        text_list (List[str]): List of detection messages
        output_path (str, optional): Output path for MP3. If None, auto-generated in tmp/
        
    Returns:
        str: Path to generated audio file
    """
    generator = AudioGenerator()
    
    if output_path is None:
        return generator.generate_audio_quick(text_list)
    else:
        return generator.generate_audio_from_alerts(text_list, output_path)

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
        
        Args:
            text (str): Raw detection text with frame numbers and confidence scores
            
        Returns:
            str: Cleaned text suitable for TTS
        """
        # Remove confidence scores
        clean = re.sub(r"\(conf: [0-9.]+\)", "", text)
        
        # Remove frame numbers
        clean = re.sub(r"\[Frame \d+\]\s*", "", clean)
        
        # Replace technical terms with natural language
        replacements = {
            "Green-traffic-lights": "Green light ahead, it's safe to cross",
            "Red-traffic-lights": "Red light ahead, stop and wait",
            "Yellow-traffic-lights": "Yellow light ahead, prepare to stop",
            "Green Light": "Green light ahead, it's safe to cross",
            "Red Light": "Red light ahead, stop and wait",
            "Yellow Light": "Yellow light ahead, prepare to stop",
            "Zebra Crossing": "Zebra crossing detected",
            "zebra crossing": "Zebra crossing detected",
            "Person on your right": "Someone is on your right side",
            "Person on your left": "Someone is on your left side",
            "Person": "Person detected",
            "Car": "Car detected",
            "Bus": "Bus detected",
            "Truck": "Truck detected",
        }
        
        for old, new in replacements.items():
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

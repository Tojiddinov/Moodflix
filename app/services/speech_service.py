"""
Speech Service module for MoodFlix application.
Handles speech recognition and text-to-speech functionality.
"""
import os
import tempfile
import time
import json
import requests
from typing import Optional
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import pygame
from pathlib import Path
import wave
import audioop

from app.core.config import settings

class SpeechService:
    """Service for handling speech recognition and text-to-speech."""
    
    def __init__(self):
        """Initialize speech recognition and text-to-speech engines."""
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = settings.SPEECH_RECOGNITION_ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 0.8
        
        # Initialize text-to-speech
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', settings.TTS_RATE)
        self.engine.setProperty('volume', settings.TTS_VOLUME)
        
        # Try to find and set a good quality voice
        voices = self.engine.getProperty('voices')
        selected_voice = None
        for voice in voices:
            # Prefer Microsoft voices if available
            if "microsoft" in voice.name.lower():
                selected_voice = voice
                break
            # Otherwise prefer female voices
            elif "female" in voice.name.lower() and not selected_voice:
                selected_voice = voice
        
        # If we found a preferred voice, use it
        if selected_voice:
            self.engine.setProperty('voice', selected_voice.id)
            print(f"Using voice: {selected_voice.name}")
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        # Check if Vosk is available for offline speech recognition
        self.vosk_available = False
        try:
            from vosk import Model, KaldiRecognizer
            
            # Check if model exists
            model_path = "vosk-model-small-en-us-0.15"
            if os.path.exists(model_path) and os.path.exists(os.path.join(model_path, "am", "final.mdl")):
                self.vosk_model = Model(model_path)
                self.vosk_available = True
                print("Vosk model initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize Vosk model: {str(e)}")
    
    def transcribe_audio(self, file_path: str) -> Optional[str]:
        """
        Transcribe audio file to text using multiple recognition methods.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Transcribed text or None if transcription failed
        """
        if not os.path.exists(file_path):
            print(f"Error: Audio file not found at {file_path}")
            return None
        
        # Try multiple recognition methods in order of preference
        transcription = None
        
        # Method 1: Try Vosk (offline) if available
        if self.vosk_available:
            transcription = self._transcribe_with_vosk(file_path)
            if transcription:
                return transcription
        
        # Method 2: Try Google Speech Recognition
        transcription = self._transcribe_with_google(file_path)
        if transcription:
            return transcription
        
        # Method 3: Try Deepgram if API key is available
        if settings.DEEPGRAM_API_KEY:
            transcription = self._transcribe_with_deepgram(file_path)
            if transcription:
                return transcription
        
        # All methods failed
        print("All transcription methods failed")
        return None
    
    def _transcribe_with_vosk(self, file_path: str) -> Optional[str]:
        """
        Transcribe audio using Vosk (offline).
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Transcribed text or None if transcription failed
        """
        try:
            from vosk import KaldiRecognizer
            
            # Open the audio file
            wf = wave.open(file_path, "rb")
            
            # Check if the audio format is compatible with Vosk
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                print("Audio file must be WAV format mono PCM")
                return None
            
            # Create recognizer
            rec = KaldiRecognizer(self.vosk_model, wf.getframerate())
            rec.SetWords(True)
            
            # Process audio
            result = ""
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    part_result = json.loads(rec.Result())
                    if "text" in part_result:
                        result += part_result["text"] + " "
            
            # Get final result
            final_result = json.loads(rec.FinalResult())
            if "text" in final_result:
                result += final_result["text"]
            
            # Return transcription if not empty
            if result.strip():
                print(f"Vosk transcription: {result}")
                return result.strip()
            else:
                print("Vosk transcription returned empty result")
                return None
                
        except Exception as e:
            print(f"Error in Vosk transcription: {str(e)}")
            return None
    
    def _transcribe_with_google(self, file_path: str) -> Optional[str]:
        """
        Transcribe audio using Google Speech Recognition.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Transcribed text or None if transcription failed
        """
        try:
            with sr.AudioFile(file_path) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
                print(f"Google transcription: {text}")
                return text
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return None
        except Exception as e:
            print(f"Error in Google transcription: {str(e)}")
            return None
    
    def _transcribe_with_deepgram(self, file_path: str) -> Optional[str]:
        """
        Transcribe audio using Deepgram API.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Transcribed text or None if transcription failed
        """
        try:
            # Prepare API request
            url = "https://api.deepgram.com/v1/listen"
            headers = {
                "Authorization": f"Token {settings.DEEPGRAM_API_KEY}"
            }
            
            # Open audio file
            with open(file_path, "rb") as f:
                audio_data = f.read()
            
            # Send request to Deepgram
            response = requests.post(
                url,
                headers=headers,
                data=audio_data,
                params={"model": "general", "language": "en-US"}
            )
            
            # Process response
            if response.status_code == 200:
                result = response.json()
                if "results" in result and "channels" in result["results"] and len(result["results"]["channels"]) > 0:
                    alternatives = result["results"]["channels"][0]["alternatives"]
                    if len(alternatives) > 0 and "transcript" in alternatives[0]:
                        transcript = alternatives[0]["transcript"]
                        print(f"Deepgram transcription: {transcript}")
                        return transcript
            
            print(f"Deepgram API error: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            print(f"Error in Deepgram transcription: {str(e)}")
            return None
    
    def speak(self, text: str) -> None:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
        """
        try:
            # Method 1: Use pyttsx3 (offline)
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error with pyttsx3 speech: {str(e)}")
            try:
                # Method 2: Fall back to gTTS (online)
                temp_dir = tempfile.mkdtemp()
                temp_file = os.path.join(temp_dir, "speech.mp3")
                
                # Generate speech
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(temp_file)
                
                # Play speech
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                # Clean up
                os.remove(temp_file)
                os.rmdir(temp_dir)
            except Exception as e2:
                print(f"Error with gTTS speech: {str(e2)}")
    
    def set_volume(self, volume: float) -> None:
        """
        Set the text-to-speech volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        # Validate volume
        volume = max(0.0, min(1.0, float(volume)))
        
        # Set volume for pyttsx3
        self.engine.setProperty('volume', volume)
        
        # Set volume for pygame
        pygame.mixer.music.set_volume(volume)
    
    def record_audio(self, duration: int = 5) -> Optional[str]:
        """
        Record audio from the microphone.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Path to the recorded audio file or None if recording failed
        """
        try:
            import sounddevice as sd
            import scipy.io.wavfile as wav
            
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, f"temp_recording_{int(time.time())}.wav")
            
            # Set recording parameters
            fs = 44100  # Sample rate
            print(f"Recording for {duration} seconds...")
            
            # Record audio
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
            sd.wait()  # Wait until recording is finished
            
            # Save as WAV file
            wav.write(temp_file, fs, recording)
            
            return temp_file
            
        except Exception as e:
            print(f"Error recording audio: {str(e)}")
            return None

"""
Voice Processor Module for Healthcare Chatbot
Handles speech-to-text and text-to-speech functionality
"""

import os
import logging
import tempfile
import wave
import io
from typing import Optional, Union, BinaryIO
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech.audio import AudioConfig
import pyttsx3
import speech_recognition as sr

from config.settings import Config

class VoiceProcessor:
    """
    Voice processor for healthcare chatbot
    Handles speech-to-text and text-to-speech using Azure Cognitive Services
    """
    
    def __init__(self):
        """Initialize the voice processor"""
        self.config = Config()
        
        # Initialize Azure Speech SDK
        if self.config.AZURE_SPEECH_KEY and self.config.AZURE_SPEECH_REGION:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.config.AZURE_SPEECH_KEY,
                region=self.config.AZURE_SPEECH_REGION
            )
            self.speech_config.speech_recognition_language = "en-GB"
            self.speech_config.speech_synthesis_voice_name = "en-GB-RyanNeural"
            self.azure_available = True
            logging.info("Azure Speech Services initialized successfully")
        else:
            self.azure_available = False
            logging.warning("Azure Speech Services not configured, using fallback options")
        
        # Initialize fallback TTS engine
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', int(150 * self.config.TTS_SPEED))
            self.tts_engine.setProperty('volume', 0.9)
            
            # Set voice (try to find a British English voice)
            voices = self.tts_engine.getProperty('voices')
            british_voice = None
            for voice in voices:
                if 'en-gb' in voice.id.lower() or 'british' in voice.name.lower():
                    british_voice = voice.id
                    break
            
            if british_voice:
                self.tts_engine.setProperty('voice', british_voice)
            
            self.fallback_tts_available = True
            logging.info("Fallback TTS engine initialized successfully")
            
        except Exception as e:
            self.fallback_tts_available = False
            logging.warning(f"Fallback TTS engine initialization failed: {str(e)}")
        
        # Initialize speech recognition
        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.fallback_stt_available = True
            logging.info("Fallback STT engine initialized successfully")
            
        except Exception as e:
            self.fallback_stt_available = False
            logging.warning(f"Fallback STT engine initialization failed: {str(e)}")
        
        logging.info("Voice Processor initialized successfully")
    
    def transcribe_audio(self, audio_file: Union[BinaryIO, str]) -> Optional[str]:
        """
        Transcribe audio to text using Azure Speech Services or fallback
        
        Args:
            audio_file: Audio file object or path
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            if self.azure_available:
                return self._transcribe_with_azure(audio_file)
            elif self.fallback_stt_available:
                return self._transcribe_with_fallback(audio_file)
            else:
                logging.error("No speech-to-text service available")
                return None
                
        except Exception as e:
            logging.error(f"Error in audio transcription: {str(e)}")
            return None
    
    def transcribe_audio_data(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio data bytes to text
        
        Args:
            audio_data: Raw audio data bytes
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Create temporary file from audio data
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Transcribe the temporary file
            result = self.transcribe_audio(temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return result
            
        except Exception as e:
            logging.error(f"Error transcribing audio data: {str(e)}")
            return None
    
    def text_to_speech(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech using Azure Speech Services or fallback
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Audio data bytes or None if failed
        """
        try:
            if self.azure_available:
                return self._synthesize_with_azure(text)
            elif self.fallback_tts_available:
                return self._synthesize_with_fallback(text)
            else:
                logging.error("No text-to-speech service available")
                return None
                
        except Exception as e:
            logging.error(f"Error in speech synthesis: {str(e)}")
            return None
    
    def _transcribe_with_azure(self, audio_file: Union[BinaryIO, str]) -> Optional[str]:
        """Transcribe audio using Azure Speech Services"""
        try:
            # Configure audio input
            if isinstance(audio_file, str):
                # File path
                audio_config = AudioConfig(filename=audio_file)
            else:
                # File object - save to temporary file first
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file.write(audio_file.read())
                    temp_file_path = temp_file.name
                
                audio_config = AudioConfig(filename=temp_file_path)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Perform recognition
            result = speech_recognizer.recognize_once()
            
            # Clean up temporary file if created
            if not isinstance(audio_file, str):
                os.unlink(temp_file_path)
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logging.warning("Azure Speech Services: No speech recognized")
                return None
            else:
                logging.warning(f"Azure Speech Services: {result.reason}")
                return None
                
        except Exception as e:
            logging.error(f"Azure transcription error: {str(e)}")
            return None
    
    def _transcribe_with_fallback(self, audio_file: Union[BinaryIO, str]) -> Optional[str]:
        """Transcribe audio using fallback speech recognition"""
        try:
            if isinstance(audio_file, str):
                # File path
                with sr.AudioFile(audio_file) as source:
                    audio = self.recognizer.record(source)
            else:
                # File object
                audio = self.recognizer.record(audio_file)
            
            # Perform recognition
            text = self.recognizer.recognize_google(audio)
            return text
            
        except sr.UnknownValueError:
            logging.warning("Fallback STT: Speech not understood")
            return None
        except sr.RequestError as e:
            logging.error(f"Fallback STT request error: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Fallback STT error: {str(e)}")
            return None
    
    def _synthesize_with_azure(self, text: str) -> Optional[bytes]:
        """Synthesize speech using Azure Speech Services"""
        try:
            # Configure speech synthesis
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config
            )
            
            # Synthesize speech
            result = speech_synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Get audio data
                audio_data = result.audio_data
                return audio_data
            else:
                logging.warning(f"Azure TTS: {result.reason}")
                return None
                
        except Exception as e:
            logging.error(f"Azure TTS error: {str(e)}")
            return None
    
    def _synthesize_with_fallback(self, text: str) -> Optional[bytes]:
        """Synthesize speech using fallback TTS engine"""
        try:
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            # Synthesize speech to file
            self.tts_engine.save_to_file(text, temp_file_path)
            self.tts_engine.runAndWait()
            
            # Read audio data from file
            with open(temp_file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return audio_data
            
        except Exception as e:
            logging.error(f"Fallback TTS error: {str(e)}")
            return None
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        voices = []
        
        if self.azure_available:
            try:
                # Get Azure voices
                speech_synthesizer = speechsdk.SpeechSynthesizer(
                    speech_config=self.speech_config
                )
                azure_voices = speech_synthesizer.get_voices_async().get()
                
                for voice in azure_voices.voices:
                    voices.append({
                        'id': voice.id,
                        'name': voice.name,
                        'locale': voice.locale,
                        'provider': 'Azure'
                    })
                    
            except Exception as e:
                logging.error(f"Error getting Azure voices: {str(e)}")
        
        if self.fallback_tts_available:
            try:
                # Get fallback voices
                fallback_voices = self.tts_engine.getProperty('voices')
                
                for voice in fallback_voices:
                    voices.append({
                        'id': voice.id,
                        'name': voice.name,
                        'provider': 'Fallback'
                    })
                    
            except Exception as e:
                logging.error(f"Error getting fallback voices: {str(e)}")
        
        return voices
    
    def set_voice(self, voice_id: str) -> bool:
        """
        Set the voice for speech synthesis
        
        Args:
            voice_id: Voice identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.azure_available:
                # Set Azure voice
                self.speech_config.speech_synthesis_voice_name = voice_id
                logging.info(f"Azure voice set to: {voice_id}")
                return True
            
            elif self.fallback_tts_available:
                # Set fallback voice
                self.tts_engine.setProperty('voice', voice_id)
                logging.info(f"Fallback voice set to: {voice_id}")
                return True
            
            else:
                logging.error("No TTS service available")
                return False
                
        except Exception as e:
            logging.error(f"Error setting voice: {str(e)}")
            return False
    
    def set_speech_rate(self, rate: float) -> bool:
        """
        Set the speech rate for TTS
        
        Args:
            rate: Speech rate multiplier (0.5 = slow, 2.0 = fast)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.fallback_tts_available:
                self.tts_engine.setProperty('rate', int(150 * rate))
                logging.info(f"Speech rate set to: {rate}")
                return True
            else:
                logging.warning("Speech rate can only be set with fallback TTS")
                return False
                
        except Exception as e:
            logging.error(f"Error setting speech rate: {str(e)}")
            return False
    
    def get_audio_format_info(self) -> dict:
        """Get information about supported audio formats"""
        return {
            'azure': {
                'formats': ['WAV', 'MP3', 'OGG'],
                'sample_rates': [8000, 16000, 22050, 44100, 48000],
                'channels': [1, 2]
            },
            'fallback': {
                'formats': ['WAV'],
                'sample_rates': [22050, 44100],
                'channels': [1, 2]
            }
        }
    
    def is_healthy(self) -> bool:
        """Check if the voice processor is healthy"""
        try:
            # Check if at least one service is available
            if not self.azure_available and not self.fallback_tts_available:
                return False
            
            # Test basic functionality
            test_text = "Hello, this is a test."
            test_audio = self.text_to_speech(test_text)
            
            if test_audio is None:
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Voice processor health check failed: {str(e)}")
            return False
    
    def get_statistics(self) -> dict:
        """Get voice processor statistics"""
        return {
            'azure_available': self.azure_available,
            'fallback_tts_available': self.fallback_tts_available,
            'fallback_stt_available': self.fallback_stt_available,
            'available_voices': len(self.get_available_voices()),
            'default_voice': self.config.DEFAULT_VOICE,
            'speech_rate': self.config.TTS_SPEED
        } 
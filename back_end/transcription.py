"""
Transcription Module using Whisper X (FREE)
"""
import whisperx
import torch
import time
from stream_config import *

class TranscriptionService:
    def __init__(self):
        self.model = None
        self.device = DEVICE
        self.compute_type = COMPUTE_TYPE
        self.model_name = WHISPER_MODEL
        self.load_model()
    
    def load_model(self):
        """
        Load Whisper X model (FREE - runs locally)
        """
        try:
            print(f"Loading Whisper X model: {self.model_name}")
            print(f"Device: {self.device}, Compute Type: {self.compute_type}")
            
            # Load Whisper X model
            self.model = whisperx.load_model(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type
            )
            
            print("Whisper X model loaded successfully!")
            return True
            
        except Exception as e:
            print(f"Error loading Whisper X model: {e}")
            print("Trying alternative approach...")
            
            # Fallback: Try with default settings
            try:
                self.model = whisperx.load_model(
                    "base",
                    device="cpu",
                    compute_type="int8"
                )
                print("Whisper X model loaded with fallback settings")
                return True
            except Exception as e2:
                print(f"Failed to load model: {e2}")
                return False
    
    def transcribe_audio(self, audio_file_path):
        """
        Transcribe audio file to text using Whisper X
        Returns: transcript text and metadata
        """
        if not self.model:
            print("Model not loaded!")
            return None
        
        try:
            print(f"Transcribing: {audio_file_path}")
            start_time = time.time()
            
            # Load audio
            audio = whisperx.load_audio(audio_file_path)
            
            # Transcribe with Whisper X
            result = self.model.transcribe(
                audio,
                batch_size=16  # Adjust based on your system
            )
            
            end_time = time.time()
            transcription_time = end_time - start_time
            
            # Extract text from segments
            transcript_text = ""
            segments = []
            
            for segment in result.get("segments", []):
                transcript_text += segment.get("text", "") + " "
                segments.append({
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'text': segment.get('text', '')
                })
            
            transcript_text = transcript_text.strip()
            
            print(f"Transcription completed in {transcription_time:.2f}s")
            print(f"Transcript length: {len(transcript_text)} characters")
            
            return {
                'text': transcript_text,
                'segments': segments,
                'language': result.get('language', 'en'),
                'transcription_time': transcription_time
            }
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return None
    
    def transcribe_with_alignment(self, audio_file_path):
        """
        Advanced transcription with word-level timestamps
        """
        if not self.model:
            return None
        
        try:
            audio = whisperx.load_audio(audio_file_path)
            result = self.model.transcribe(audio, batch_size=16)
            
            # Load alignment model
            model_a, metadata = whisperx.load_align_model(
                language_code=result["language"],
                device=self.device
            )
            
            # Align whisper output
            result_aligned = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                self.device,
                return_char_alignments=False
            )
            
            return result_aligned
            
        except Exception as e:
            print(f"Alignment error: {e}")
            # Fallback to basic transcription
            return self.transcribe_audio(audio_file_path)
    
    def get_model_info(self):
        """
        Get information about loaded model
        """
        return {
            'model_name': self.model_name,
            'device': self.device,
            'compute_type': self.compute_type,
            'is_loaded': self.model is not None
        }

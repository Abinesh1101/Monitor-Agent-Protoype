"""
Summarization Service using Hugging Face Transformers (FREE)
"""
from transformers import pipeline
import time
from stream_config import MAX_SUMMARY_LENGTH

class SummarizationService:
    def __init__(self):
        self.summarizer = None
        self.load_model()
    
    def load_model(self):
        """
        Load Facebook BART summarization model (FREE)
        """
        try:
            print("Loading summarization model (BART)...")
            print("First time will download ~1.6GB model...")
            
            # Load BART summarization pipeline
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1  # CPU (use 0 for GPU)
            )
            
            print("✅ Summarization model loaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error loading summarization model: {e}")
            # Fallback to smaller model
            try:
                print("Trying smaller model (DistilBART)...")
                self.summarizer = pipeline(
                    "summarization",
                    model="sshleifer/distilbart-cnn-12-6",
                    device=-1
                )
                print("✅ Smaller model loaded successfully!")
                return True
            except Exception as e2:
                print(f"❌ Fallback also failed: {e2}")
                return False
    
    def generate_summary(self, transcript_text, max_words=15):
        """
        Generate a short summary from transcript
        Args:
            transcript_text: Full transcript text
            max_words: Maximum words in summary (default: 15)
        Returns:
            Summary text (15 words or less)
        """
        if not self.summarizer:
            print("Model not loaded!")
            return "Summary unavailable"
        
        if not transcript_text or len(transcript_text.strip()) == 0:
            return "No content to summarize"
        
        try:
            print(f"Generating summary for {len(transcript_text)} characters...")
            start_time = time.time()
            
            # Handle short text
            if len(transcript_text.split()) < 30:
                # Text too short to summarize, return first 15 words
                words = transcript_text.split()[:max_words]
                return " ".join(words)
            
            # Calculate max_length for model (in tokens, roughly 0.75 * words)
            max_length = int(max_words * 1.3)  # ~15 words = ~20 tokens
            min_length = max(5, max_length - 5)
            
            # Generate summary
            summary_result = self.summarizer(
                transcript_text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                truncation=True
            )
            
            summary_text = summary_result[0]['summary_text']
            
            # Ensure it's within word limit
            words = summary_text.split()
            if len(words) > max_words:
                summary_text = " ".join(words[:max_words])
            
            end_time = time.time()
            summarization_time = end_time - start_time
            
            print(f"✅ Summary generated in {summarization_time:.2f}s")
            print(f"Summary ({len(summary_text.split())} words): {summary_text}")
            
            return summary_text
            
        except Exception as e:
            print(f"❌ Summarization error: {e}")
            # Fallback: Return first 15 words
            words = transcript_text.split()[:max_words]
            return " ".join(words)
    
    def batch_summarize(self, transcripts):
        """
        Summarize multiple transcripts at once
        Args:
            transcripts: List of transcript texts
        Returns:
            List of summaries
        """
        summaries = []
        for i, transcript in enumerate(transcripts):
            print(f"Summarizing transcript {i+1}/{len(transcripts)}...")
            summary = self.generate_summary(transcript)
            summaries.append(summary)
        return summaries
    
    def get_model_info(self):
        """
        Get information about loaded model
        """
        return {
            'model_loaded': self.summarizer is not None,
            'max_summary_words': MAX_SUMMARY_LENGTH,
            'model_name': 'facebook/bart-large-cnn' if self.summarizer else 'Not loaded'
        }

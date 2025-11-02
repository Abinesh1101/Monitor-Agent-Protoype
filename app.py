"""
Main Flask Application - Monitor Agent Prototype
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
from datetime import datetime
import json
import os
import traceback

# Import our modules
from stream_config import *
from stream_handler import StreamHandler
from transcription import TranscriptionService
from summarization import SummarizationService

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize services
stream_handler = StreamHandler()
transcription_service = TranscriptionService()
summarization_service = SummarizationService()

# Store all records
records = []
monitoring_active = False
monitor_thread = None

def process_stream_chunk():
    """
    Process one chunk: extract audio -> transcribe -> summarize
    """
    global records
    
    try:
        # Extract audio chunk
        print("\n" + "="*50)
        print("📹 Extracting audio chunk...")
        chunk_data = stream_handler.extract_audio_chunk()
        
        if not chunk_data:
            print("❌ Failed to extract audio chunk")
            return None
        
        audio_file = chunk_data['file_path']
        timestamp = chunk_data['timestamp']
        
        # Calculate video times
        video_start_time = f"{(chunk_data['chunk_number']-1) * CHUNK_DURATION // 60:02d}:{(chunk_data['chunk_number']-1) * CHUNK_DURATION % 60:02d}"
        video_end_time = f"{chunk_data['chunk_number'] * CHUNK_DURATION // 60:02d}:{chunk_data['chunk_number'] * CHUNK_DURATION % 60:02d}"
        
        # Transcribe audio
        print("🎤 Transcribing audio...")
        transcript_data = transcription_service.transcribe_audio(audio_file)
        
        if not transcript_data:
            print("❌ Transcription failed")
            return None
        
        transcript_text = transcript_data['text']
        
        # Generate summary
        print("🤖 Generating AI summary...")
        summary = summarization_service.generate_summary(transcript_text, MAX_SUMMARY_LENGTH)
        
        # Create record
        record = {
            'id': len(records) + 1,
            'date_time': datetime.now().strftime("%d %b, %I:%M %p"),
            'video_time_start': video_start_time,
            'video_time_end': video_end_time,
            'transcript': transcript_text,
            'summary': summary,
            'audio_file': audio_file,
            'processing_time': {
                'extraction': chunk_data['extraction_time'],
                'transcription': transcript_data['transcription_time']
            }
        }
        
        records.append(record)
        
        print("✅ Record created successfully!")
        print(f"Transcript: {transcript_text[:100]}...")
        print(f"Summary: {summary}")
        print("="*50 + "\n")
        
        # Save to file
        save_records()
        
        return record
        
    except Exception as e:
        print(f"❌ Error processing chunk: {e}")
        traceback.print_exc()
        return None

def monitoring_loop():
    """
    Main monitoring loop - runs in background thread
    """
    global monitoring_active
    
    print("\n🚀 Starting monitoring loop...")
    
    while monitoring_active:
        try:
            # Process one chunk
            process_stream_chunk()
            
            # Small delay between chunks
            if monitoring_active:
                time.sleep(2)  # 2 second gap between chunks
                
        except Exception as e:
            print(f"❌ Error in monitoring loop: {e}")
            traceback.print_exc()
            time.sleep(5)
    
    print("🛑 Monitoring loop stopped")

def save_records():
    """
    Save records to JSON file
    """
    try:
        output_file = os.path.join(OUTPUTS_DIR, 'records.json')
        with open(output_file, 'w') as f:
            json.dump(records, f, indent=2)
        print(f"💾 Records saved to {output_file}")
    except Exception as e:
        print(f"❌ Error saving records: {e}")

# ============= API ENDPOINTS =============

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """
    Start the monitoring process
    """
    global monitoring_active, monitor_thread
    
    try:
        print("\n📥 Received START request")
        
        if monitoring_active:
            return jsonify({
                'success': False,
                'message': 'Monitoring already active'
            }), 400
        
        # Get request data safely
        try:
            data = request.get_json(silent=True) or {}
        except Exception as e:
            print(f"Warning: Could not parse JSON body: {e}")
            data = {}
        
        m3u8_url = data.get('m3u8_url', None)
        
        if m3u8_url:
            stream_handler.m3u8_url = m3u8_url
            print(f"Using provided M3U8 URL: {m3u8_url}")
        
        # Start stream
        print("🎬 Starting stream...")
        if not stream_handler.start_stream():
            return jsonify({
                'success': False,
                'message': 'Failed to start stream. Could not find M3U8 link. Please check the stream URL.'
            }), 500
        
        # Start monitoring thread
        monitoring_active = True
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
        
        print("✅ Monitoring started successfully!")
        
        return jsonify({
            'success': True,
            'message': 'Monitoring started successfully',
            'm3u8_url': stream_handler.m3u8_url
        })
        
    except Exception as e:
        print(f"❌ Error in start_monitoring: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error starting monitoring: {str(e)}'
        }), 500

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """
    Stop the monitoring process
    """
    global monitoring_active
    
    try:
        print("\n📥 Received STOP request")
        
        if not monitoring_active:
            return jsonify({
                'success': False,
                'message': 'Monitoring not active'
            }), 400
        
        monitoring_active = False
        stream_handler.stop_stream()
        
        print("✅ Monitoring stopped successfully!")
        
        return jsonify({
            'success': True,
            'message': 'Monitoring stopped successfully'
        })
        
    except Exception as e:
        print(f"❌ Error in stop_monitoring: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error stopping monitoring: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Get current monitoring status
    """
    try:
        stream_status = stream_handler.get_status()
        
        return jsonify({
            'monitoring_active': monitoring_active,
            'total_records': len(records),
            'stream_status': stream_status,
            'models': {
                'transcription': transcription_service.get_model_info(),
                'summarization': summarization_service.get_model_info()
            }
        })
    except Exception as e:
        print(f"❌ Error in get_status: {e}")
        return jsonify({
            'monitoring_active': False,
            'total_records': 0,
            'error': str(e)
        }), 500

@app.route('/api/records', methods=['GET'])
def get_records():
    """
    Get all processed records
    """
    try:
        return jsonify({
            'success': True,
            'count': len(records),
            'records': records
        })
    except Exception as e:
        print(f"❌ Error in get_records: {e}")
        return jsonify({
            'success': False,
            'count': 0,
            'records': [],
            'error': str(e)
        }), 500

@app.route('/api/records/latest', methods=['GET'])
def get_latest_record():
    """
    Get the most recent record
    """
    try:
        if len(records) == 0:
            return jsonify({
                'success': False,
                'message': 'No records available'
            }), 404
        
        return jsonify({
            'success': True,
            'record': records[-1]
        })
    except Exception as e:
        print(f"❌ Error in get_latest_record: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'services': {
            'flask': True,
            'stream_handler': stream_handler is not None,
            'transcription': transcription_service.model is not None,
            'summarization': summarization_service.summarizer is not None
        }
    })

@app.route('/')
def index():
    """
    Basic info endpoint
    """
    return jsonify({
        'name': 'Monitor Agent Prototype',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': [
            '/api/start',
            '/api/stop',
            '/api/status',
            '/api/records',
            '/api/records/latest',
            '/api/health'
        ]
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 MONITOR AGENT PROTOTYPE - STARTING")
    print("="*60)
    print(f"📡 Server: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"🎥 Stream: {STREAM_URL}")
    print(f"⏱️  Chunk Duration: {CHUNK_DURATION} seconds")
    print(f"📝 Transcription: Whisper X ({WHISPER_MODEL})")
    print(f"🤖 Summarization: BART (max {MAX_SUMMARY_LENGTH} words)")
    print("="*60 + "\n")
    
    # Run Flask app
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=True,
        threaded=True
    )
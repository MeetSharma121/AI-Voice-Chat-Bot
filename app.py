#!/usr/bin/env python3
"""
AI Voice Chatbot with LLM & RAG for Healthcare
Main Flask application entry point
"""

import os
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import core modules
from core.chatbot import HealthcareChatbot
from core.voice_processor import VoiceProcessor
from core.rag_engine import RAGEngine
from config.settings import Config
from utils.logger import setup_logger
from utils.monitoring import setup_monitoring

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app)

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup logging and monitoring
setup_logger()
setup_monitoring(app)

# Initialize core components
chatbot = HealthcareChatbot()
voice_processor = VoiceProcessor()
rag_engine = RAGEngine()

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle text-based chat requests"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Process message through RAG and LLM
        response = chatbot.process_message(user_message, session_id)
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'timestamp': chatbot.get_timestamp()
        })
        
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/voice/transcribe', methods=['POST'])
def transcribe_audio():
    """Handle audio transcription requests"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'Audio file is required'}), 400
        
        audio_file = request.files['audio']
        session_id = request.form.get('session_id', 'default')
        
        # Transcribe audio to text
        transcribed_text = voice_processor.transcribe_audio(audio_file)
        
        if not transcribed_text:
            return jsonify({'error': 'Could not transcribe audio'}), 400
        
        # Process transcribed text through chatbot
        response = chatbot.process_message(transcribed_text, session_id)
        
        # Convert response to speech
        audio_response = voice_processor.text_to_speech(response)
        
        return jsonify({
            'transcribed_text': transcribed_text,
            'response': response,
            'audio_response': audio_response,
            'session_id': session_id
        })
        
    except Exception as e:
        logging.error(f"Error in voice transcription: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/voice/synthesize', methods=['POST'])
def synthesize_speech():
    """Convert text to speech"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Convert text to speech
        audio_data = voice_processor.text_to_speech(text)
        
        return jsonify({
            'audio_data': audio_data,
            'text_length': len(text)
        })
        
    except Exception as e:
        logging.error(f"Error in speech synthesis: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'services': {
            'chatbot': chatbot.is_healthy(),
            'voice_processor': voice_processor.is_healthy(),
            'rag_engine': rag_engine.is_healthy()
        }
    })

@app.route('/api/knowledge', methods=['GET'])
def get_knowledge_base():
    """Get information about the knowledge base"""
    try:
        knowledge_info = rag_engine.get_knowledge_base_info()
        return jsonify(knowledge_info)
    except Exception as e:
        logging.error(f"Error getting knowledge base info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# SocketIO events for real-time communication
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logging.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logging.info(f"Client disconnected: {request.sid}")

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle real-time chat messages"""
    try:
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        # Process message
        response = chatbot.process_message(user_message, session_id)
        
        # Emit response back to client
        emit('chat_response', {
            'response': response,
            'session_id': session_id,
            'timestamp': chatbot.get_timestamp()
        })
        
    except Exception as e:
        logging.error(f"Error handling chat message: {str(e)}")
        emit('error', {'error': 'Internal server error'})

@socketio.on('voice_message')
def handle_voice_message(data):
    """Handle real-time voice messages"""
    try:
        audio_data = data.get('audio_data', '')
        session_id = data.get('session_id', 'default')
        
        # Process audio data
        transcribed_text = voice_processor.transcribe_audio_data(audio_data)
        response = chatbot.process_message(transcribed_text, session_id)
        
        # Emit response back to client
        emit('voice_response', {
            'transcribed_text': transcribed_text,
            'response': response,
            'session_id': session_id
        })
        
    except Exception as e:
        logging.error(f"Error handling voice message: {str(e)}")
        emit('error', {'error': 'Internal server error'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logging.info(f"Starting Healthcare Chatbot on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug) 
#!/usr/bin/env python3
"""
Simplified AI Voice Chatbot for Healthcare
Basic version that can run with minimal dependencies
"""

import os
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS
CORS(app)

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*")

# Simple logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleHealthcareChatbot:
    """Simplified healthcare chatbot"""
    
    def __init__(self):
        self.conversations = {}
        self.system_prompt = """You are EMMA (Electronic Medical Management Assistant), a healthcare assistant designed to help patients with general inquiries, appointment booking, and basic health information.

IMPORTANT SAFETY GUIDELINES:
1. NEVER provide medical diagnosis or treatment advice
2. NEVER prescribe medications
3. ALWAYS recommend consulting healthcare professionals for medical concerns
4. Focus on administrative tasks, general information, and appointment management
5. Be empathetic, professional, and compliant with NHS guidelines
6. If asked about symptoms, always recommend seeing a doctor
7. For emergencies, direct to emergency services (999)

Your capabilities include:
- Answering general health questions using NHS guidelines
- Helping with appointment booking and scheduling
- Providing information about services and facilities
- Answering administrative questions
- Directing to appropriate healthcare resources

Always respond in a helpful, professional manner while maintaining safety compliance."""
        
        # Sample NHS knowledge base
        self.nhs_knowledge = {
            'appointments': [
                'You can book an appointment by calling your GP surgery, using the NHS app, or visiting their website.',
                'Many surgeries offer online booking systems for convenience.',
                'For urgent care, call 111 or visit your nearest urgent care centre.',
                'GP appointments are typically available within 48 hours for urgent cases.',
                'You can book routine appointments up to 4 weeks in advance.'
            ],
            'emergencies': [
                'For medical emergencies, call 999 immediately.',
                'For urgent but non-emergency care, call 111.',
                'A&E departments are available 24/7 for serious emergencies.',
                'Minor injuries units can treat sprains, cuts, and minor burns.',
                'Call 111 for advice on whether you need emergency care.'
            ],
            'prescriptions': [
                'You can request repeat prescriptions through your GP surgery or local pharmacy.',
                'Allow 48 hours for prescription processing.',
                'The NHS app can also be used for prescription requests.',
                'Some pharmacies offer prescription collection and delivery services.',
                'Prescription charges apply to working-age adults in England.'
            ],
            'registration': [
                'To register with a GP surgery, visit in person with proof of identity and address.',
                'Some surgeries offer online registration.',
                'You can find nearby GP surgeries on the NHS website.',
                'You can register with any GP surgery in your area.',
                'Temporary registration is available if you\'re away from home.'
            ],
            'costs': [
                'NHS treatment is free at the point of use for UK residents.',
                'Prescription charges apply in England (£9.65 per item).',
                'Dental treatment has charges but they\'re lower than private care.',
                'Eye tests are free for children, over-60s, and those with certain conditions.',
                'Travel vaccinations may have charges depending on the type.'
            ],
            'services': [
                'The NHS provides comprehensive healthcare including GP, hospital, and specialist care.',
                'Mental health services are available through your GP and specialist teams.',
                'Maternity care is free and comprehensive for pregnant women.',
                'Children\'s services include vaccinations, health checks, and dental care.',
                'Preventive services like screenings and vaccinations are widely available.'
            ]
        }
    
    def process_message(self, user_message: str, session_id: str = "default") -> str:
        """Process a user message and generate a response"""
        try:
            logger.info(f"Processing message for session {session_id}: {user_message[:100]}...")
            
            # Add message to conversation history
            self._add_to_conversation(session_id, "user", user_message)
            
            # Generate response
            response = self._generate_response(user_message, session_id)
            
            # Add response to conversation history
            self._add_to_conversation(session_id, "assistant", response)
            
            logger.info(f"Generated response for session {session_id}: {response[:100]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I'm experiencing technical difficulties. Please try again or contact our support team for assistance."
    
    def _generate_response(self, user_message: str, session_id: str = "default") -> str:
        """Generate response based on user message"""
        user_message_lower = user_message.lower()
        
        # Get conversation context for more natural responses
        conversation_context = self._get_conversation_context(session_id)
        
        # Check for mental health queries FIRST (before greetings)
        if any(word in user_message_lower for word in ['mental health', 'anxiety', 'depression', 'counseling', 'therapy', 'stress', 'worried']):
            return "Mental health support is available through the NHS. You can speak to your GP about mental health concerns, who can refer you to appropriate services. There are also crisis helplines available 24/7. For immediate support, you can call the Samaritans at 116 123 or text SHOUT to 85258."
        
        # Check for vaccination queries
        elif any(word in user_message_lower for word in ['vaccination', 'vaccine', 'immunization', 'vaccinated', 'jab']):
            return "Vaccinations are an important part of preventive healthcare. You can book vaccination appointments through your GP surgery, local pharmacy, or the NHS app. Many vaccinations are free on the NHS. For specific vaccination schedules or eligibility, please contact your GP or visit the NHS website."
        
        # Check for blood test queries
        elif any(word in user_message_lower for word in ['blood test', 'test results', 'laboratory', 'lab', 'testing']):
            return "For blood tests and laboratory services, you'll need a referral from your GP. Test results are typically available within 1-2 weeks and will be sent to your GP surgery. You can also check some results through the NHS app. For urgent results, your GP will contact you directly."
        
        # Check for dental queries
        elif any(word in user_message_lower for word in ['dental', 'dentist', 'teeth', 'tooth', 'oral']):
            return "Dental care on the NHS is available for children, pregnant women, and those on certain benefits. For adults, NHS dental treatment has charges, but they're lower than private care. You can find NHS dentists through the NHS website or by calling 111. Emergency dental care is available for severe pain."
        
        # Check for pharmacy queries
        elif any(word in user_message_lower for word in ['pharmacy', 'chemist', 'medication', 'drugs', 'tablets']):
            return "Pharmacies provide medication, health advice, and some services like flu vaccinations. Many are open late and on weekends. You can get emergency contraception, emergency medication, and advice without an appointment. For prescription medication, you'll need a prescription from your GP or other healthcare provider."
        
        # Check for appointment-related queries
        if any(word in user_message_lower for word in ['appointment', 'book', 'schedule', 'visit', 'see doctor']):
            if 'urgent' in user_message_lower or 'emergency' in user_message_lower:
                return "For urgent appointments, " + self.nhs_knowledge['appointments'][3] + " If it's a medical emergency, " + self.nhs_knowledge['emergencies'][0] + " Otherwise, " + self.nhs_knowledge['appointments'][0] + " How urgent is your situation?"
            else:
                return "I can help you with appointment booking. " + self.nhs_knowledge['appointments'][0] + " " + self.nhs_knowledge['appointments'][4] + " What type of appointment do you need?"
        
        # Check for emergency-related queries
        elif any(word in user_message_lower for word in ['emergency', 'urgent', '999', 'pain', 'serious', 'severe']):
            if '999' in user_message_lower or 'emergency' in user_message_lower:
                return "For medical emergencies, " + self.nhs_knowledge['emergencies'][0] + " " + self.nhs_knowledge['emergencies'][4] + " If you're experiencing severe symptoms, please call 999 immediately."
            else:
                return "For urgent but non-emergency care, " + self.nhs_knowledge['emergencies'][1] + " " + self.nhs_knowledge['emergencies'][3] + " " + self.nhs_knowledge['emergencies'][4]
        
        # Check for prescription-related queries
        elif any(word in user_message_lower for word in ['prescription', 'medication', 'medicine', 'repeat', 'drugs']):
            if 'cost' in user_message_lower or 'charge' in user_message_lower or 'money' in user_message_lower:
                return "For prescription costs, " + self.nhs_knowledge['costs'][1] + " " + self.nhs_knowledge['prescriptions'][0] + " " + self.nhs_knowledge['prescriptions'][4] + " Do you have any questions about prescription charges?"
            else:
                return "For prescription requests, " + self.nhs_knowledge['prescriptions'][0] + " " + self.nhs_knowledge['prescriptions'][3] + " " + self.nhs_knowledge['prescriptions'][2] + " What type of prescription do you need?"
        
        # Check for registration-related queries
        elif any(word in user_message_lower for word in ['register', 'new patient', 'gp', 'surgery', 'join']):
            if 'temporary' in user_message_lower or 'away' in user_message_lower:
                return "For temporary registration, " + self.nhs_knowledge['registration'][4] + " " + self.nhs_knowledge['registration'][0] + " " + self.nhs_knowledge['registration'][3] + " This is useful when you're away from home for extended periods."
            else:
                return "To register with a GP surgery, " + self.nhs_knowledge['registration'][0] + " " + self.nhs_knowledge['registration'][2] + " " + self.nhs_knowledge['registration'][3] + " Do you have your proof of identity and address ready?"
        
        # Check for greeting
        elif any(word in user_message_lower for word in ['hello', 'hi', 'help', 'start', 'begin']):
            return "Hello! I'm EMMA, your healthcare assistant. I can help with appointment booking, general health information, and administrative questions. How can I assist you today?"
        
        # Check for symptoms
        elif any(word in user_message_lower for word in ['symptom', 'pain', 'ill', 'sick', 'hurt', 'ache', 'feeling unwell']):
            return "I understand you're experiencing health concerns. For medical symptoms and diagnosis, please consult with a healthcare professional. I can help with administrative tasks like appointment booking and general information."
        
        # Check for non-healthcare queries and redirect appropriately
        elif any(word in user_message_lower for word in ['weather', 'california', 'temperature', 'forecast', 'sunny', 'rain']):
            return "I'm EMMA, a healthcare assistant focused on NHS services and medical administrative tasks. I can't provide weather information, but I can help you with healthcare-related questions like appointment booking, prescription requests, or general NHS information. How can I assist you with healthcare matters?"
        
        elif any(word in user_message_lower for word in ['sports', 'football', 'basketball', 'game', 'team', 'score']):
            return "I'm EMMA, your healthcare assistant. While I can't provide sports information, I'm here to help with healthcare administrative tasks, appointment booking, and NHS-related questions. How can I assist you with your healthcare needs?"
        
        elif any(word in user_message_lower for word in ['news', 'politics', 'current events', 'election', 'government']):
            return "I'm EMMA, a healthcare assistant. I focus on helping with NHS services, appointment booking, and healthcare administrative tasks. For news and current events, I'd recommend checking news websites. How can I help you with healthcare-related questions?"
        
        # Check for specific healthcare topics and provide detailed responses
        elif any(word in user_message_lower for word in ['vaccination', 'vaccine', 'immunization', 'vaccinated', 'jab']):
            return "Vaccinations are an important part of preventive healthcare. You can book vaccination appointments through your GP surgery, local pharmacy, or the NHS app. Many vaccinations are free on the NHS. For specific vaccination schedules or eligibility, please contact your GP or visit the NHS website."
        
        elif any(word in user_message_lower for word in ['blood test', 'test results', 'laboratory', 'lab', 'testing']):
            return "For blood tests and laboratory services, you'll need a referral from your GP. Test results are typically available within 1-2 weeks and will be sent to your GP surgery. You can also check some results through the NHS app. For urgent results, your GP will contact you directly."
        
        elif any(word in user_message_lower for word in ['dental', 'dentist', 'teeth', 'tooth', 'oral']):
            return "Dental care on the NHS is available for children, pregnant women, and those on certain benefits. For adults, NHS dental treatment has charges, but they're lower than private care. You can find NHS dentists through the NHS website or by calling 111. Emergency dental care is available for severe pain."
        
        elif any(word in user_message_lower for word in ['mental health', 'anxiety', 'depression', 'counseling', 'therapy', 'stress', 'worried']):
            return "Mental health support is available through the NHS. You can speak to your GP about mental health concerns, who can refer you to appropriate services. There are also crisis helplines available 24/7. For immediate support, you can call the Samaritans at 116 123 or text SHOUT to 85258."
        
        elif any(word in user_message_lower for word in ['pharmacy', 'chemist', 'medication', 'drugs', 'tablets']):
            return "Pharmacies provide medication, health advice, and some services like flu vaccinations. Many are open late and on weekends. You can get emergency contraception, emergency medication, and advice without an appointment. For prescription medication, you'll need a prescription from your GP or other healthcare provider."
        
        # Check for general health information requests
        elif any(word in user_message_lower for word in ['healthy', 'diet', 'exercise', 'lifestyle', 'fitness', 'nutrition']):
            return "Maintaining a healthy lifestyle is important for overall wellbeing. The NHS provides guidance on healthy eating, exercise recommendations, and lifestyle advice. You can find detailed information on the NHS website, or speak to your GP for personalized advice. Remember, I can help with administrative tasks like booking appointments for health checkups."
        
        # Check for cost-related queries
        elif any(word in user_message_lower for word in ['cost', 'charge', 'free', 'payment', 'money', 'expensive', 'cheap']):
            return "NHS treatment is generally free at the point of use for UK residents. " + self.nhs_knowledge['costs'][1] + " " + self.nhs_knowledge['costs'][2] + " " + self.nhs_knowledge['costs'][3] + " For specific cost information, please contact your GP surgery or the relevant NHS service."
        
        # Check for service-related queries
        elif any(word in user_message_lower for word in ['service', 'available', 'what can', 'help with', 'offer', 'provide']):
            return "The NHS provides comprehensive healthcare services. " + self.nhs_knowledge['services'][0] + " " + self.nhs_knowledge['services'][1] + " " + self.nhs_knowledge['services'][2] + " " + self.nhs_knowledge['services'][3] + " " + self.nhs_knowledge['services'][4] + " What specific service are you looking for?"
        
        # Default response with more helpful guidance
        else:
            return "Thank you for your message. I'm EMMA, your healthcare assistant, and I'm here to help with NHS services and healthcare administrative tasks. I can assist with appointment booking, prescription requests, registration, and general healthcare information. For specific medical concerns, please consult with a healthcare professional. What healthcare-related question can I help you with today?"
    
    def _add_to_conversation(self, session_id: str, role: str, content: str):
        """Add message to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        self.conversations[session_id].append(message)
    
    def get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()
    
    def is_healthy(self) -> bool:
        """Check if the chatbot is healthy"""
        return True

    def _get_conversation_context(self, session_id: str) -> list:
        """Get recent conversation context for more natural responses"""
        if session_id in self.conversations:
            return self.conversations[session_id][-3:]  # Last 3 messages
        return []

# Initialize chatbot
chatbot = SimpleHealthcareChatbot()

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
        
        # Process message
        response = chatbot.process_message(user_message, session_id)
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'timestamp': chatbot.get_timestamp()
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'services': {
            'chatbot': chatbot.is_healthy()
        },
        'timestamp': chatbot.get_timestamp()
    })

@app.route('/api/knowledge', methods=['GET'])
def get_knowledge_base():
    """Get information about the knowledge base"""
    return jsonify({
        'total_categories': len(chatbot.nhs_knowledge),
        'categories': list(chatbot.nhs_knowledge.keys()),
        'timestamp': chatbot.get_timestamp()
    })

# SocketIO events for real-time communication
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

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
        logger.error(f"Error handling chat message: {str(e)}")
        emit('error', {'error': 'Internal server error'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # Changed from 5000 to 5001
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Simplified Healthcare Chatbot on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug) 
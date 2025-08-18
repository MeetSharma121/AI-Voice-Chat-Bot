"""
Healthcare Chatbot Core Module
Handles conversation logic, LLM integration, and safety compliance
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import openai
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate

from config.settings import Config
from core.safety_checker import SafetyChecker
from core.conversation_manager import ConversationManager
from utils.encryption import encrypt_data, decrypt_data

class HealthcareChatbot:
    """
    Main chatbot class for healthcare assistance
    Implements LLM integration, safety checks, and conversation management
    """
    
    def __init__(self):
        """Initialize the healthcare chatbot"""
        self.config = Config()
        self.safety_checker = SafetyChecker()
        self.conversation_manager = ConversationManager()
        
        # Initialize OpenAI client
        if self.config.OPENAI_API_KEY:
            openai.api_key = self.config.OPENAI_API_KEY
            self.llm = ChatOpenAI(
                model_name=self.config.OPENAI_MODEL,
                temperature=self.config.OPENAI_TEMPERATURE,
                max_tokens=self.config.OPENAI_MAX_TOKENS
            )
        else:
            self.llm = None
            logging.warning("OpenAI API key not provided. LLM functionality disabled.")
        
        # System prompt for healthcare assistance
        self.system_prompt = self._create_system_prompt()
        
        # Conversation history
        self.conversations: Dict[str, List[Dict]] = {}
        
        # Safety thresholds
        self.safety_threshold = 0.8
        self.max_conversation_length = 50
        
        logging.info("Healthcare Chatbot initialized successfully")
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for healthcare assistance"""
        return """You are EMMA (Electronic Medical Management Assistant), a healthcare assistant designed to help patients with general inquiries, appointment booking, and basic health information.

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

    def process_message(self, user_message: str, session_id: str = "default") -> str:
        """
        Process a user message and generate a response
        
        Args:
            user_message: The user's input message
            session_id: Unique session identifier
            
        Returns:
            Generated response from the chatbot
        """
        try:
            # Log the incoming message
            logging.info(f"Processing message for session {session_id}: {user_message[:100]}...")
            
            # Safety check
            safety_score = self.safety_checker.check_message_safety(user_message)
            if safety_score < self.safety_threshold:
                logging.warning(f"Message flagged for safety concerns. Score: {safety_score}")
                return self._get_safety_response()
            
            # Add message to conversation history
            self._add_to_conversation(session_id, "user", user_message)
            
            # Generate response using LLM
            if self.llm:
                response = self._generate_llm_response(user_message, session_id)
            else:
                response = self._generate_fallback_response(user_message)
            
            # Safety check on response
            response_safety_score = self.safety_checker.check_message_safety(response)
            if response_safety_score < self.safety_threshold:
                logging.warning(f"Response flagged for safety concerns. Score: {response_safety_score}")
                response = self._get_safety_response()
            
            # Add response to conversation history
            self._add_to_conversation(session_id, "assistant", response)
            
            # Log the response
            logging.info(f"Generated response for session {session_id}: {response[:100]}...")
            
            return response
            
        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            return self._get_error_response()
    
    def _generate_llm_response(self, user_message: str, session_id: str) -> str:
        """Generate response using the LLM"""
        try:
            # Get conversation context
            context = self._get_conversation_context(session_id)
            
            # Create messages for LLM
            messages = [
                SystemMessage(content=self.system_prompt),
                *context,
                HumanMessage(content=user_message)
            ]
            
            # Generate response
            response = self.llm(messages)
            
            return response.content
            
        except Exception as e:
            logging.error(f"Error generating LLM response: {str(e)}")
            return self._generate_fallback_response(user_message)
    
    def _generate_fallback_response(self, user_message: str) -> str:
        """Generate fallback response when LLM is unavailable"""
        # Simple rule-based responses for common queries
        user_message_lower = user_message.lower()
        
        if any(word in user_message_lower for word in ['appointment', 'book', 'schedule']):
            return "I can help you with appointment booking. Please provide your preferred date and time, and I'll check availability. For medical concerns, please consult with your healthcare provider."
        
        elif any(word in user_message_lower for word in ['symptom', 'pain', 'ill', 'sick']):
            return "I understand you're experiencing health concerns. For medical symptoms and diagnosis, please consult with a healthcare professional. I can help with administrative tasks like appointment booking."
        
        elif any(word in user_message_lower for word in ['hello', 'hi', 'help']):
            return "Hello! I'm EMMA, your healthcare assistant. I can help with appointment booking, general health information, and administrative questions. How can I assist you today?"
        
        else:
            return "Thank you for your message. I'm here to help with healthcare administrative tasks. For medical concerns, please consult with a healthcare professional. How can I assist you?"
    
    def _get_conversation_context(self, session_id: str, max_messages: int = 5) -> List:
        """Get recent conversation context for the LLM"""
        if session_id not in self.conversations:
            return []
        
        # Get recent messages
        recent_messages = self.conversations[session_id][-max_messages:]
        
        # Convert to LangChain message format
        context = []
        for msg in recent_messages:
            if msg['role'] == 'user':
                context.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                context.append(SystemMessage(content=msg['content']))
        
        return context
    
    def _add_to_conversation(self, session_id: str, role: str, content: str):
        """Add message to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        # Check conversation length limit
        if len(self.conversations[session_id]) >= self.max_conversation_length:
            # Remove oldest messages
            self.conversations[session_id] = self.conversations[session_id][-self.max_conversation_length//2:]
        
        # Add new message
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        # Encrypt sensitive content if needed
        if self.config.GDPR_COMPLIANCE:
            message['content'] = encrypt_data(content, self.config.ENCRYPTION_KEY)
        
        self.conversations[session_id].append(message)
    
    def _get_safety_response(self) -> str:
        """Return a safe, compliant response"""
        return "I apologize, but I cannot provide that information. For medical concerns, please consult with a healthcare professional. I'm here to help with administrative tasks like appointment booking."
    
    def _get_error_response(self) -> str:
        """Return an error response"""
        return "I'm experiencing technical difficulties. Please try again or contact our support team for assistance."
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        if session_id not in self.conversations:
            return []
        
        # Decrypt content if needed
        history = []
        for msg in self.conversations[session_id]:
            decrypted_msg = msg.copy()
            if self.config.GDPR_COMPLIANCE:
                try:
                    decrypted_msg['content'] = decrypt_data(msg['content'], self.config.ENCRYPTION_KEY)
                except:
                    decrypted_msg['content'] = "[Encrypted content]"
            history.append(decrypted_msg)
        
        return history
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            logging.info(f"Cleared conversation history for session {session_id}")
    
    def get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()
    
    def is_healthy(self) -> bool:
        """Check if the chatbot is healthy"""
        try:
            # Basic health checks
            if self.llm and not self.config.OPENAI_API_KEY:
                return False
            
            # Check if safety checker is working
            test_score = self.safety_checker.check_message_safety("Hello")
            if test_score < 0:
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Health check failed: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get chatbot statistics"""
        total_conversations = len(self.conversations)
        total_messages = sum(len(conv) for conv in self.conversations.values())
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'active_sessions': len([conv for conv in self.conversations.values() if len(conv) > 0]),
            'timestamp': self.get_timestamp()
        } 
"""
Conversation Manager Module for Healthcare Chatbot
Handles conversation state, context, and session management
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid

@dataclass
class Message:
    """Message data structure"""
    id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]
    safety_score: Optional[float] = None

@dataclass
class Conversation:
    """Conversation data structure"""
    id: str
    session_id: str
    user_id: Optional[str]
    start_time: datetime
    last_activity: datetime
    messages: List[Message]
    context: Dict[str, Any]
    status: str  # 'active', 'paused', 'ended'
    metadata: Dict[str, Any]

class ConversationManager:
    """
    Manages conversations, sessions, and context for the healthcare chatbot
    """
    
    def __init__(self):
        """Initialize the conversation manager"""
        self.conversations: Dict[str, Conversation] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.max_conversation_length = 100
        self.max_session_duration = timedelta(hours=24)
        self.cleanup_interval = timedelta(hours=1)
        self.last_cleanup = datetime.now()
        
        logging.info("Conversation Manager initialized successfully")
    
    def create_conversation(self, session_id: str, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation
        
        Args:
            session_id: Unique session identifier
            user_id: Optional user identifier
            
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        
        conversation = Conversation(
            id=conversation_id,
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.now(),
            last_activity=datetime.now(),
            messages=[],
            context={
                'topic': 'general',
                'intent': 'greeting',
                'entities': [],
                'sentiment': 'neutral'
            },
            status='active',
            metadata={
                'platform': 'web',
                'language': 'en',
                'timezone': 'UTC'
            }
        )
        
        self.conversations[conversation_id] = conversation
        
        # Update session
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'conversation_ids': [],
                'created_at': datetime.now(),
                'last_activity': datetime.now()
            }
        
        self.sessions[session_id]['conversation_ids'].append(conversation_id)
        self.sessions[session_id]['last_activity'] = datetime.now()
        
        logging.info(f"Created conversation {conversation_id} for session {session_id}")
        return conversation_id
    
    def add_message(self, conversation_id: str, role: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None, 
                   safety_score: Optional[float] = None) -> bool:
        """
        Add a message to a conversation
        
        Args:
            conversation_id: ID of the conversation
            role: Role of the message sender ('user' or 'assistant')
            content: Message content
            metadata: Optional message metadata
            safety_score: Optional safety score
            
        Returns:
            True if successful, False otherwise
        """
        if conversation_id not in self.conversations:
            logging.error(f"Conversation {conversation_id} not found")
            return False
        
        conversation = self.conversations[conversation_id]
        
        # Check conversation length limit
        if len(conversation.messages) >= self.max_conversation_length:
            logging.warning(f"Conversation {conversation_id} reached maximum length")
            return False
        
        # Create message
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {},
            safety_score=safety_score
        )
        
        # Add message to conversation
        conversation.messages.append(message)
        conversation.last_activity = datetime.now()
        
        # Update context based on message
        self._update_conversation_context(conversation, message)
        
        # Update session activity
        session_id = conversation.session_id
        if session_id in self.sessions:
            self.sessions[session_id]['last_activity'] = datetime.now()
        
        logging.debug(f"Added message to conversation {conversation_id}")
        return True
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def get_conversation_by_session(self, session_id: str) -> Optional[Conversation]:
        """Get the most recent conversation for a session"""
        if session_id not in self.sessions:
            return None
        
        conversation_ids = self.sessions[session_id]['conversation_ids']
        if not conversation_ids:
            return None
        
        # Return the most recent conversation
        latest_id = conversation_ids[-1]
        return self.conversations.get(latest_id)
    
    def get_conversation_history(self, conversation_id: str, 
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history
        
        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        if conversation_id not in self.conversations:
            return []
        
        conversation = self.conversations[conversation_id]
        messages = conversation.messages
        
        if limit:
            messages = messages[-limit:]
        
        # Convert to dictionaries
        history = []
        for message in messages:
            message_dict = asdict(message)
            message_dict['timestamp'] = message.timestamp.isoformat()
            history.append(message_dict)
        
        return history
    
    def update_conversation_context(self, conversation_id: str, 
                                  context_updates: Dict[str, Any]) -> bool:
        """
        Update conversation context
        
        Args:
            conversation_id: ID of the conversation
            context_updates: Dictionary of context updates
            
        Returns:
            True if successful, False otherwise
        """
        if conversation_id not in self.conversations:
            return False
        
        conversation = self.conversations[conversation_id]
        conversation.context.update(context_updates)
        conversation.last_activity = datetime.now()
        
        logging.debug(f"Updated context for conversation {conversation_id}")
        return True
    
    def pause_conversation(self, conversation_id: str) -> bool:
        """Pause a conversation"""
        if conversation_id not in self.conversations:
            return False
        
        conversation = self.conversations[conversation_id]
        conversation.status = 'paused'
        conversation.last_activity = datetime.now()
        
        logging.info(f"Paused conversation {conversation_id}")
        return True
    
    def resume_conversation(self, conversation_id: str) -> bool:
        """Resume a paused conversation"""
        if conversation_id not in self.conversations:
            return False
        
        conversation = self.conversations[conversation_id]
        conversation.status = 'active'
        conversation.last_activity = datetime.now()
        
        logging.info(f"Resumed conversation {conversation_id}")
        return True
    
    def end_conversation(self, conversation_id: str) -> bool:
        """End a conversation"""
        if conversation_id not in self.conversations:
            return False
        
        conversation = self.conversations[conversation_id]
        conversation.status = 'ended'
        conversation.last_activity = datetime.now()
        
        logging.info(f"Ended conversation {conversation_id}")
        return True
    
    def get_active_conversations(self) -> List[Conversation]:
        """Get all active conversations"""
        return [conv for conv in self.conversations.values() if conv.status == 'active']
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a summary of a conversation"""
        if conversation_id not in self.conversations:
            return {}
        
        conversation = self.conversations[conversation_id]
        
        summary = {
            'id': conversation.id,
            'session_id': conversation.session_id,
            'user_id': conversation.user_id,
            'start_time': conversation.start_time.isoformat(),
            'last_activity': conversation.last_activity.isoformat(),
            'message_count': len(conversation.messages),
            'status': conversation.status,
            'context': conversation.context,
            'duration': (conversation.last_activity - conversation.start_time).total_seconds()
        }
        
        return summary
    
    def cleanup_old_conversations(self):
        """Clean up old conversations and sessions"""
        now = datetime.now()
        
        # Clean up old sessions
        expired_sessions = []
        for session_id, session_data in self.sessions.items():
            if now - session_data['last_activity'] > self.max_session_duration:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self._cleanup_session(session_id)
        
        # Clean up old conversations
        expired_conversations = []
        for conv_id, conversation in self.conversations.items():
            if now - conversation.last_activity > self.max_session_duration:
                expired_conversations.append(conv_id)
        
        for conv_id in expired_conversations:
            del self.conversations[conv_id]
        
        self.last_cleanup = now
        
        if expired_sessions or expired_conversations:
            logging.info(f"Cleaned up {len(expired_sessions)} sessions and {len(expired_conversations)} conversations")
    
    def _cleanup_session(self, session_id: str):
        """Clean up a specific session"""
        if session_id in self.sessions:
            # Remove associated conversations
            conversation_ids = self.sessions[session_id]['conversation_ids']
            for conv_id in conversation_ids:
                if conv_id in self.conversations:
                    del self.conversations[conv_id]
            
            # Remove session
            del self.sessions[session_id]
    
    def _update_conversation_context(self, conversation: Conversation, message: Message):
        """Update conversation context based on new message"""
        # Simple context updates - in a real implementation, this would use NLP
        if message.role == 'user':
            # Update topic based on keywords
            content_lower = message.content.lower()
            
            if any(word in content_lower for word in ['appointment', 'book', 'schedule']):
                conversation.context['topic'] = 'appointment_booking'
                conversation.context['intent'] = 'book_appointment'
            
            elif any(word in content_lower for word in ['symptom', 'pain', 'ill']):
                conversation.context['topic'] = 'health_inquiry'
                conversation.context['intent'] = 'health_question'
            
            elif any(word in content_lower for word in ['hello', 'hi', 'help']):
                conversation.context['topic'] = 'greeting'
                conversation.context['intent'] = 'greeting'
            
            # Update sentiment (simplified)
            positive_words = ['good', 'great', 'excellent', 'happy', 'fine']
            negative_words = ['bad', 'terrible', 'awful', 'sad', 'pain']
            
            if any(word in content_lower for word in positive_words):
                conversation.context['sentiment'] = 'positive'
            elif any(word in content_lower for word in negative_words):
                conversation.context['sentiment'] = 'negative'
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get conversation manager statistics"""
        now = datetime.now()
        
        total_conversations = len(self.conversations)
        active_conversations = len(self.get_active_conversations())
        total_sessions = len(self.sessions)
        
        # Calculate average conversation length
        if total_conversations > 0:
            total_messages = sum(len(conv.messages) for conv in self.conversations.values())
            avg_conversation_length = total_messages / total_conversations
        else:
            avg_conversation_length = 0
        
        return {
            'total_conversations': total_conversations,
            'active_conversations': active_conversations,
            'total_sessions': total_sessions,
            'average_conversation_length': avg_conversation_length,
            'last_cleanup': self.last_cleanup.isoformat(),
            'timestamp': now.isoformat()
        }
    
    def export_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Export a conversation for analysis or backup"""
        if conversation_id not in self.conversations:
            return None
        
        conversation = self.conversations[conversation_id]
        
        export_data = {
            'conversation': asdict(conversation),
            'messages': [asdict(msg) for msg in conversation.messages],
            'export_timestamp': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        # Convert datetime objects to ISO format
        export_data['conversation']['start_time'] = conversation.start_time.isoformat()
        export_data['conversation']['last_activity'] = conversation.last_activity.isoformat()
        
        for msg in export_data['messages']:
            msg['timestamp'] = msg['timestamp'].isoformat()
        
        return export_data
    
    def is_healthy(self) -> bool:
        """Check if the conversation manager is healthy"""
        try:
            # Basic health checks
            if not isinstance(self.conversations, dict):
                return False
            
            if not isinstance(self.sessions, dict):
                return False
            
            # Check if cleanup is working
            if self.last_cleanup > datetime.now():
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Conversation manager health check failed: {str(e)}")
            return False 
"""
RAG Engine Module for Healthcare Chatbot
Handles retrieval-augmented generation using vector databases and embeddings
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from datetime import datetime

# Import vector database clients
try:
    import pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logging.warning("Pinecone not available, using FAISS fallback")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available")

# Import embedding models
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("Sentence Transformers not available")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available")

from config.settings import Config

class RAGEngine:
    """
    Retrieval-Augmented Generation engine for healthcare chatbot
    Uses vector databases and embeddings to provide relevant context
    """
    
    def __init__(self):
        """Initialize the RAG engine"""
        self.config = Config()
        
        # Initialize vector database
        self.vector_db = self._initialize_vector_database()
        
        # Initialize embedding model
        self.embedding_model = self._initialize_embedding_model()
        
        # Knowledge base
        self.knowledge_base = self._load_knowledge_base()
        
        # Configuration
        self.chunk_size = self.config.CHUNK_SIZE
        self.chunk_overlap = self.config.CHUNK_OVERLAP
        self.top_k = self.config.TOP_K_RESULTS
        
        logging.info("RAG Engine initialized successfully")
    
    def _initialize_vector_database(self):
        """Initialize vector database (Pinecone or FAISS)"""
        if PINECONE_AVAILABLE and self.config.PINECONE_API_KEY:
            try:
                pinecone.init(
                    api_key=self.config.PINECONE_API_KEY,
                    environment=self.config.PINECONE_ENVIRONMENT
                )
                
                # Check if index exists, create if not
                if self.config.PINECONE_INDEX_NAME not in pinecone.list_indexes():
                    pinecone.create_index(
                        name=self.config.PINECONE_INDEX_NAME,
                        dimension=1536,  # OpenAI embedding dimension
                        metric='cosine'
                    )
                
                index = pinecone.Index(self.config.PINECONE_INDEX_NAME)
                logging.info("Pinecone vector database initialized successfully")
                return {'type': 'pinecone', 'index': index}
                
            except Exception as e:
                logging.error(f"Pinecone initialization failed: {str(e)}")
        
        if FAISS_AVAILABLE:
            try:
                # Create FAISS index
                dimension = 1536 if OPENAI_AVAILABLE else 768  # Default to sentence-transformers dimension
                index = faiss.IndexFlatIP(dimension)
                
                # Load existing vectors if available
                if os.path.exists('data/faiss_index.idx'):
                    index = faiss.read_index('data/faiss_index.idx')
                    logging.info("Loaded existing FAISS index")
                
                logging.info("FAISS vector database initialized successfully")
                return {'type': 'faiss', 'index': index, 'vectors': [], 'metadata': []}
                
            except Exception as e:
                logging.error(f"FAISS initialization failed: {str(e)}")
        
        logging.warning("No vector database available, RAG functionality disabled")
        return None
    
    def _initialize_embedding_model(self):
        """Initialize embedding model"""
        if OPENAI_AVAILABLE and self.config.OPENAI_API_KEY:
            try:
                openai.api_key = self.config.OPENAI_API_KEY
                logging.info("OpenAI embedding model initialized")
                return {'type': 'openai', 'model': self.config.EMBEDDING_MODEL}
                
            except Exception as e:
                logging.error(f"OpenAI embedding model initialization failed: {str(e)}")
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                model = SentenceTransformer('all-MiniLM-L6-v2')
                logging.info("Sentence Transformers embedding model initialized")
                return {'type': 'sentence_transformers', 'model': model}
                
            except Exception as e:
                logging.error(f"Sentence Transformers initialization failed: {str(e)}")
        
        logging.warning("No embedding model available, RAG functionality disabled")
        return None
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load healthcare knowledge base"""
        knowledge_base = {
            'documents': [],
            'faqs': [],
            'guidelines': [],
            'last_updated': None
        }
        
        # Load sample NHS data
        sample_data = self._get_sample_nhs_data()
        knowledge_base.update(sample_data)
        
        # Load from files if available
        if os.path.exists('data/knowledge_base.json'):
            try:
                with open('data/knowledge_base.json', 'r') as f:
                    file_data = json.load(f)
                    knowledge_base.update(file_data)
                    logging.info("Loaded knowledge base from file")
            except Exception as e:
                logging.error(f"Error loading knowledge base file: {str(e)}")
        
        return knowledge_base
    
    def _get_sample_nhs_data(self) -> Dict[str, Any]:
        """Get sample NHS healthcare data"""
        return {
            'faqs': [
                {
                    'question': 'How do I book an appointment with my GP?',
                    'answer': 'You can book an appointment by calling your GP surgery, using the NHS app, or visiting their website. Many surgeries also offer online booking systems.',
                    'category': 'appointments',
                    'tags': ['gp', 'appointment', 'booking']
                },
                {
                    'question': 'What should I do if I have a medical emergency?',
                    'answer': 'For medical emergencies, call 999 immediately. For urgent but non-emergency care, call 111 or visit your nearest urgent care centre.',
                    'category': 'emergencies',
                    'tags': ['emergency', '999', 'urgent care']
                },
                {
                    'question': 'How do I get a repeat prescription?',
                    'answer': 'You can request a repeat prescription through your GP surgery, local pharmacy, or using the NHS app. Allow 48 hours for processing.',
                    'category': 'prescriptions',
                    'tags': ['prescription', 'repeat', 'medication']
                },
                {
                    'question': 'What are the opening hours for my local pharmacy?',
                    'answer': 'Pharmacy opening hours vary. You can find your nearest pharmacy and their opening hours using the NHS website or by calling 111.',
                    'category': 'pharmacies',
                    'tags': ['pharmacy', 'opening hours', 'medication']
                },
                {
                    'question': 'How do I register with a new GP surgery?',
                    'answer': 'To register with a new GP surgery, visit the surgery in person with proof of identity and address. You can also register online through some surgeries.',
                    'category': 'registration',
                    'tags': ['gp', 'registration', 'new patient']
                }
            ],
            'guidelines': [
                {
                    'title': 'NHS Appointments Policy',
                    'content': 'The NHS aims to provide appointments within 48 hours for urgent cases and within 18 weeks for non-urgent referrals. Patients should contact their GP for non-emergency care.',
                    'category': 'appointments',
                    'tags': ['nhs', 'appointments', 'policy', 'waiting times']
                },
                {
                    'title': 'Patient Privacy and Confidentiality',
                    'content': 'All patient information is confidential and protected under GDPR and NHS data protection regulations. Information is only shared with consent or when legally required.',
                    'category': 'privacy',
                    'tags': ['gdpr', 'confidentiality', 'data protection', 'privacy']
                },
                {
                    'title': 'Emergency Care Guidelines',
                    'content': 'Emergency care is available 24/7 through A&E departments and ambulance services. Call 999 for life-threatening emergencies. Use 111 for urgent advice.',
                    'category': 'emergencies',
                    'tags': ['emergency', '999', '111', 'a&e', 'urgent care']
                }
            ]
        }
    
    def get_relevant_context(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query using vector similarity search
        
        Args:
            query: The user query
            top_k: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        if not self.vector_db or not self.embedding_model:
            logging.warning("RAG engine not available, returning empty context")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            if query_embedding is None:
                return []
            
            # Search vector database
            if top_k is None:
                top_k = self.top_k
            
            if self.vector_db['type'] == 'pinecone':
                results = self._search_pinecone(query_embedding, top_k)
            elif self.vector_db['type'] == 'faiss':
                results = self._search_faiss(query_embedding, top_k)
            else:
                results = []
            
            # Add knowledge base results
            kb_results = self._search_knowledge_base(query, top_k)
            results.extend(kb_results)
            
            # Sort by relevance and return top results
            results.sort(key=lambda x: x.get('score', 0), reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logging.error(f"Error retrieving context: {str(e)}")
            return []
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        try:
            if self.embedding_model['type'] == 'openai':
                response = openai.Embedding.create(
                    input=text,
                    model=self.embedding_model['model']
                )
                return response['data'][0]['embedding']
            
            elif self.embedding_model['type'] == 'sentence_transformers':
                embedding = self.embedding_model['model'].encode(text)
                return embedding.tolist()
            
            else:
                return None
                
        except Exception as e:
            logging.error(f"Error generating embedding: {str(e)}")
            return None
    
    def _search_pinecone(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Search Pinecone vector database"""
        try:
            results = self.vector_db['index'].query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            documents = []
            for match in results.matches:
                documents.append({
                    'id': match.id,
                    'score': match.score,
                    'metadata': match.metadata,
                    'source': 'pinecone'
                })
            
            return documents
            
        except Exception as e:
            logging.error(f"Pinecone search error: {str(e)}")
            return []
    
    def _search_faiss(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Search FAISS vector database"""
        try:
            if len(self.vector_db['vectors']) == 0:
                return []
            
            # Convert to numpy array
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            # Search
            scores, indices = self.vector_db['index'].search(query_vector, top_k)
            
            documents = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.vector_db['metadata']):
                    documents.append({
                        'id': f"faiss_{idx}",
                        'score': float(score),
                        'metadata': self.vector_db['metadata'][idx],
                        'source': 'faiss'
                    })
            
            return documents
            
        except Exception as e:
            logging.error(f"FAISS search error: {str(e)}")
            return []
    
    def _search_knowledge_base(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search knowledge base using keyword matching"""
        try:
            results = []
            query_lower = query.lower()
            
            # Search FAQs
            for faq in self.knowledge_base['faqs']:
                score = self._calculate_keyword_score(query_lower, faq)
                if score > 0.1:  # Threshold for relevance
                    results.append({
                        'id': f"faq_{len(results)}",
                        'score': score,
                        'metadata': {
                            'type': 'faq',
                            'question': faq['question'],
                            'answer': faq['answer'],
                            'category': faq['category'],
                            'tags': faq['tags']
                        },
                        'source': 'knowledge_base'
                    })
            
            # Search guidelines
            for guideline in self.knowledge_base['guidelines']:
                score = self._calculate_keyword_score(query_lower, guideline)
                if score > 0.1:
                    results.append({
                        'id': f"guideline_{len(results)}",
                        'score': score,
                        'metadata': {
                            'type': 'guideline',
                            'title': guideline['title'],
                            'content': guideline['content'],
                            'category': guideline['category'],
                            'tags': guideline['tags']
                        },
                        'source': 'knowledge_base'
                    })
            
            return results
            
        except Exception as e:
            logging.error(f"Knowledge base search error: {str(e)}")
            return []
    
    def _calculate_keyword_score(self, query: str, document: Dict[str, Any]) -> float:
        """Calculate relevance score based on keyword matching"""
        score = 0.0
        
        # Check question/title
        if 'question' in document:
            text = document['question'].lower()
        elif 'title' in document:
            text = document['title'].lower()
        else:
            text = ""
        
        # Check content
        if 'content' in document:
            text += " " + document['content'].lower()
        elif 'answer' in document:
            text += " " + document['answer'].lower()
        
        # Check tags
        if 'tags' in document:
            tags = " ".join(document['tags']).lower()
            text += " " + tags
        
        # Calculate score based on word overlap
        query_words = set(query.split())
        text_words = set(text.split())
        
        if text_words:
            overlap = len(query_words.intersection(text_words))
            score = overlap / len(query_words)
        
        return score
    
    def add_document(self, document: Dict[str, Any]) -> bool:
        """
        Add a document to the knowledge base and vector database
        
        Args:
            document: Document with content and metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embedding for document content
            content = document.get('content', '')
            if not content:
                logging.error("Document has no content")
                return False
            
            embedding = self._generate_embedding(content)
            if embedding is None:
                return False
            
            # Add to vector database
            if self.vector_db['type'] == 'pinecone':
                success = self._add_to_pinecone(document, embedding)
            elif self.vector_db['type'] == 'faiss':
                success = self._add_to_faiss(document, embedding)
            else:
                success = False
            
            if success:
                # Add to knowledge base
                self.knowledge_base['documents'].append(document)
                self.knowledge_base['last_updated'] = datetime.now().isoformat()
                
                # Save to file
                self._save_knowledge_base()
                
                logging.info(f"Document added successfully: {document.get('title', 'Unknown')}")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error adding document: {str(e)}")
            return False
    
    def _add_to_pinecone(self, document: Dict[str, Any], embedding: List[float]) -> bool:
        """Add document to Pinecone"""
        try:
            doc_id = f"doc_{len(self.knowledge_base['documents'])}"
            
            self.vector_db['index'].upsert(
                vectors=[(doc_id, embedding, document)]
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Error adding to Pinecone: {str(e)}")
            return False
    
    def _add_to_faiss(self, document: Dict[str, Any], embedding: List[float]) -> bool:
        """Add document to FAISS"""
        try:
            # Add to FAISS index
            self.vector_db['index'].add(np.array([embedding], dtype=np.float32))
            
            # Store metadata
            self.vector_db['metadata'].append(document)
            self.vector_db['vectors'].append(embedding)
            
            # Save index
            faiss.write_index(self.vector_db['index'], 'data/faiss_index.idx')
            
            return True
            
        except Exception as e:
            logging.error(f"Error adding to FAISS: {str(e)}")
            return False
    
    def _save_knowledge_base(self):
        """Save knowledge base to file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/knowledge_base.json', 'w') as f:
                json.dump(self.knowledge_base, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving knowledge base: {str(e)}")
    
    def get_knowledge_base_info(self) -> Dict[str, Any]:
        """Get information about the knowledge base"""
        return {
            'total_documents': len(self.knowledge_base['documents']),
            'total_faqs': len(self.knowledge_base['faqs']),
            'total_guidelines': len(self.knowledge_base['guidelines']),
            'vector_database': self.vector_db['type'] if self.vector_db else 'none',
            'embedding_model': self.embedding_model['type'] if self.embedding_model else 'none',
            'last_updated': self.knowledge_base['last_updated'],
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'top_k_results': self.top_k
        }
    
    def is_healthy(self) -> bool:
        """Check if the RAG engine is healthy"""
        try:
            # Check if vector database is available
            if not self.vector_db:
                return False
            
            # Check if embedding model is available
            if not self.embedding_model:
                return False
            
            # Test basic functionality
            test_query = "appointment booking"
            test_context = self.get_relevant_context(test_query, top_k=1)
            
            if test_context is None:
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"RAG engine health check failed: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get RAG engine statistics"""
        return {
            'vector_database_type': self.vector_db['type'] if self.vector_db else 'none',
            'embedding_model_type': self.embedding_model['type'] if self.embedding_model else 'none',
            'knowledge_base_size': len(self.knowledge_base['documents']),
            'faq_count': len(self.knowledge_base['faqs']),
            'guideline_count': len(self.knowledge_base['guidelines']),
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'top_k_results': self.top_k
        } 
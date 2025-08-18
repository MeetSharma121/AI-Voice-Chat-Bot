"""
Safety Checker Module for Healthcare Chatbot
Ensures compliance with healthcare standards and filters inappropriate content
"""

import re
import logging
from typing import List, Dict, Tuple
from datetime import datetime

class SafetyChecker:
    """
    Safety checker for healthcare chatbot
    Implements content filtering and compliance checking
    """
    
    def __init__(self):
        """Initialize the safety checker"""
        self.risk_keywords = self._load_risk_keywords()
        self.medical_terms = self._load_medical_terms()
        self.compliance_rules = self._load_compliance_rules()
        
        # Safety thresholds
        self.high_risk_threshold = 0.9
        self.medium_risk_threshold = 0.7
        self.low_risk_threshold = 0.5
        
        logging.info("Safety Checker initialized successfully")
    
    def _load_risk_keywords(self) -> Dict[str, List[str]]:
        """Load risk keywords for different categories"""
        return {
            'high_risk': [
                'diagnose', 'diagnosis', 'treat', 'treatment', 'prescribe', 'prescription',
                'cure', 'heal', 'medicine', 'medication', 'drug', 'surgery', 'operation',
                'emergency', 'urgent', 'critical', 'serious', 'dangerous', 'fatal'
            ],
            'medium_risk': [
                'symptom', 'pain', 'ache', 'hurt', 'sick', 'ill', 'disease', 'condition',
                'infection', 'virus', 'bacteria', 'cancer', 'tumor', 'heart attack',
                'stroke', 'diabetes', 'hypertension', 'asthma'
            ],
            'low_risk': [
                'appointment', 'schedule', 'book', 'visit', 'consultation', 'checkup',
                'routine', 'preventive', 'vaccination', 'immunization', 'screening'
            ]
        }
    
    def _load_medical_terms(self) -> List[str]:
        """Load medical terminology for context analysis"""
        return [
            'nhs', 'gp', 'doctor', 'physician', 'nurse', 'specialist', 'consultant',
            'hospital', 'clinic', 'practice', 'surgery', 'pharmacy', 'laboratory',
            'test', 'examination', 'scan', 'x-ray', 'blood test', 'urine test'
        ]
    
    def _load_compliance_rules(self) -> Dict[str, List[str]]:
        """Load compliance rules for different healthcare standards"""
        return {
            'gdpr': [
                'personal data', 'patient information', 'medical record', 'privacy',
                'consent', 'data protection', 'confidentiality'
            ],
            'nhs': [
                'nhs guidelines', 'nhs policy', 'nhs standards', 'nhs protocol',
                'nhs framework', 'nhs regulation'
            ],
            'hipaa': [
                'protected health information', 'phi', 'health insurance portability',
                'accountability act', 'privacy rule', 'security rule'
            ]
        }
    
    def check_message_safety(self, message: str) -> float:
        """
        Check the safety score of a message
        
        Args:
            message: The message to check
            
        Returns:
            Safety score between 0.0 (unsafe) and 1.0 (safe)
        """
        try:
            if not message or not isinstance(message, str):
                return 0.0
            
            message_lower = message.lower()
            
            # Calculate risk scores for different categories
            high_risk_score = self._calculate_risk_score(message_lower, 'high_risk')
            medium_risk_score = self._calculate_risk_score(message_lower, 'medium_risk')
            low_risk_score = self._calculate_risk_score(message_lower, 'low_risk')
            
            # Calculate overall safety score
            safety_score = self._calculate_overall_safety(
                high_risk_score, medium_risk_score, low_risk_score
            )
            
            # Apply compliance checks
            compliance_score = self._check_compliance(message_lower)
            safety_score = min(safety_score, compliance_score)
            
            # Log safety check results
            logging.debug(f"Safety check for message: {message[:50]}... Score: {safety_score:.2f}")
            
            return safety_score
            
        except Exception as e:
            logging.error(f"Error in safety check: {str(e)}")
            return 0.0
    
    def _calculate_risk_score(self, message: str, risk_level: str) -> float:
        """Calculate risk score for a specific risk level"""
        if risk_level not in self.risk_keywords:
            return 0.0
        
        keywords = self.risk_keywords[risk_level]
        found_keywords = []
        
        for keyword in keywords:
            if keyword in message:
                found_keywords.append(keyword)
        
        # Calculate risk based on keyword frequency and context
        if not found_keywords:
            return 1.0
        
        # Check for context that might reduce risk
        context_score = self._analyze_context(message, found_keywords)
        
        # Calculate base risk score
        base_risk = len(found_keywords) / len(keywords)
        
        # Apply context adjustment
        adjusted_risk = base_risk * context_score
        
        return max(0.0, 1.0 - adjusted_risk)
    
    def _analyze_context(self, message: str, keywords: List[str]) -> float:
        """Analyze context to determine if keywords are used safely"""
        context_score = 1.0
        
        # Check for safe usage patterns
        safe_patterns = [
            r'not\s+\w+',  # "not diagnose", "not treat"
            r'cannot\s+\w+',  # "cannot diagnose", "cannot treat"
            r'will\s+not\s+\w+',  # "will not diagnose", "will not treat"
            r'should\s+not\s+\w+',  # "should not diagnose", "should not treat"
            r'do\s+not\s+\w+',  # "do not diagnose", "do not treat"
            r'information\s+about',  # "information about symptoms"
            r'general\s+information',  # "general information about"
            r'nhs\s+guidelines',  # "NHS guidelines about"
            r'consult\s+a\s+doctor',  # "consult a doctor"
            r'see\s+a\s+healthcare\s+professional'  # "see a healthcare professional"
        ]
        
        for pattern in safe_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                context_score *= 0.5  # Reduce risk if safe pattern found
        
        # Check for medical context that might increase risk
        medical_context = any(term in message.lower() for term in self.medical_terms)
        if medical_context:
            # Medical context might increase risk for certain keywords
            high_risk_medical = ['diagnose', 'treat', 'prescribe', 'cure']
            if any(keyword in keywords for keyword in high_risk_medical):
                context_score *= 0.3  # Increase risk for medical context with high-risk keywords
        
        return context_score
    
    def _calculate_overall_safety(self, high_risk: float, medium_risk: float, low_risk: float) -> float:
        """Calculate overall safety score from individual risk scores"""
        # Weighted combination of risk scores
        # High risk has highest weight, low risk has lowest weight
        weighted_score = (
            high_risk * 0.6 +      # 60% weight for high risk
            medium_risk * 0.3 +    # 30% weight for medium risk
            low_risk * 0.1         # 10% weight for low risk
        )
        
        return weighted_score
    
    def _check_compliance(self, message: str) -> float:
        """Check compliance with healthcare standards"""
        compliance_score = 1.0
        
        # Check GDPR compliance
        if self._check_gdpr_compliance(message):
            compliance_score *= 0.8
        
        # Check NHS compliance
        if self._check_nhs_compliance(message):
            compliance_score *= 0.9
        
        # Check HIPAA compliance (if applicable)
        if self._check_hipaa_compliance(message):
            compliance_score *= 0.85
        
        return compliance_score
    
    def _check_gdpr_compliance(self, message: str) -> bool:
        """Check GDPR compliance"""
        gdpr_keywords = self.compliance_rules['gdpr']
        return any(keyword in message for keyword in gdpr_keywords)
    
    def _check_nhs_compliance(self, message: str) -> bool:
        """Check NHS compliance"""
        nhs_keywords = self.compliance_rules['nhs']
        return any(keyword in message for keyword in nhs_keywords)
    
    def _check_hipaa_compliance(self, message: str) -> bool:
        """Check HIPAA compliance"""
        hipaa_keywords = self.compliance_rules['hipaa']
        return any(keyword in message for keyword in hipaa_keywords)
    
    def get_safety_report(self, message: str) -> Dict:
        """Get detailed safety report for a message"""
        safety_score = self.check_message_safety(message)
        
        report = {
            'message': message[:100] + '...' if len(message) > 100 else message,
            'safety_score': safety_score,
            'risk_level': self._get_risk_level(safety_score),
            'flagged_keywords': self._get_flagged_keywords(message),
            'compliance_issues': self._get_compliance_issues(message),
            'recommendations': self._get_safety_recommendations(safety_score),
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _get_risk_level(self, safety_score: float) -> str:
        """Get risk level based on safety score"""
        if safety_score >= self.high_risk_threshold:
            return 'LOW'
        elif safety_score >= self.medium_risk_threshold:
            return 'MEDIUM'
        elif safety_score >= self.low_risk_threshold:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    def _get_flagged_keywords(self, message: str) -> List[str]:
        """Get list of flagged keywords in the message"""
        flagged = []
        message_lower = message.lower()
        
        for risk_level, keywords in self.risk_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    flagged.append({
                        'keyword': keyword,
                        'risk_level': risk_level
                    })
        
        return flagged
    
    def _get_compliance_issues(self, message: str) -> List[str]:
        """Get list of compliance issues in the message"""
        issues = []
        message_lower = message.lower()
        
        for standard, keywords in self.compliance_rules.items():
            for keyword in keywords:
                if keyword in message_lower:
                    issues.append(f"{standard.upper()}: {keyword}")
        
        return issues
    
    def _get_safety_recommendations(self, safety_score: float) -> List[str]:
        """Get safety recommendations based on safety score"""
        recommendations = []
        
        if safety_score < self.low_risk_threshold:
            recommendations.extend([
                "Message contains high-risk content",
                "Review and potentially block this message",
                "Consider human review for compliance"
            ])
        elif safety_score < self.medium_risk_threshold:
            recommendations.extend([
                "Message contains medium-risk content",
                "Monitor this type of content closely",
                "Consider adding safety disclaimers"
            ])
        elif safety_score < self.high_risk_threshold:
            recommendations.extend([
                "Message contains low-risk content",
                "Continue monitoring for safety",
                "Consider adding informational disclaimers"
            ])
        else:
            recommendations.append("Message appears safe for healthcare context")
        
        return recommendations
    
    def is_healthy(self) -> bool:
        """Check if the safety checker is healthy"""
        try:
            # Test with safe message
            safe_score = self.check_message_safety("Hello, how can I help you?")
            if safe_score < 0.5:
                return False
            
            # Test with risky message
            risky_score = self.check_message_safety("I want to diagnose your condition")
            if risky_score > 0.5:
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Safety checker health check failed: {str(e)}")
            return False 
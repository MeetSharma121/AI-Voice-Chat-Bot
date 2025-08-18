"""
Encryption Utility Module for Healthcare Chatbot
Provides encryption/decryption for GDPR compliance and data security
"""

import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional, Union

def generate_key(password: str, salt: Optional[bytes] = None) -> tuple:
    """
    Generate encryption key from password
    
    Args:
        password: Password string
        salt: Optional salt bytes
        
    Returns:
        Tuple of (key, salt)
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_data(data: str, password: str, salt: Optional[bytes] = None) -> str:
    """
    Encrypt data using password-based encryption
    
    Args:
        data: Data string to encrypt
        password: Password for encryption
        salt: Optional salt bytes
        
    Returns:
        Encrypted data as base64 string
    """
    try:
        key, salt = generate_key(password, salt)
        fernet = Fernet(key)
        
        encrypted_data = fernet.encrypt(data.encode())
        
        # Combine salt and encrypted data
        combined = salt + encrypted_data
        return base64.urlsafe_b64encode(combined).decode()
        
    except Exception as e:
        logging.error(f"Encryption failed: {str(e)}")
        raise

def decrypt_data(encrypted_data: str, password: str) -> Optional[str]:
    """
    Decrypt data using password-based decryption
    
    Args:
        encrypted_data: Encrypted data as base64 string
        password: Password for decryption
        
    Returns:
        Decrypted data string or None if failed
    """
    try:
        # Decode base64
        combined = base64.urlsafe_b64decode(encrypted_data.encode())
        
        # Extract salt and encrypted data
        salt = combined[:16]
        encrypted = combined[16:]
        
        # Generate key
        key, _ = generate_key(password, salt)
        fernet = Fernet(key)
        
        # Decrypt
        decrypted_data = fernet.decrypt(encrypted)
        return decrypted_data.decode()
        
    except Exception as e:
        logging.error(f"Decryption failed: {str(e)}")
        return None

def encrypt_file(input_path: str, output_path: str, password: str) -> bool:
    """
    Encrypt a file
    
    Args:
        input_path: Path to input file
        output_path: Path to output encrypted file
        password: Password for encryption
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(input_path, 'rb') as f:
            data = f.read()
        
        encrypted_data = encrypt_data(data.decode('utf-8'), password)
        
        with open(output_path, 'w') as f:
            f.write(encrypted_data)
        
        logging.info(f"File encrypted successfully: {input_path} -> {output_path}")
        return True
        
    except Exception as e:
        logging.error(f"File encryption failed: {str(e)}")
        return False

def decrypt_file(input_path: str, output_path: str, password: str) -> bool:
    """
    Decrypt a file
    
    Args:
        input_path: Path to input encrypted file
        output_path: Path to output decrypted file
        password: Password for decryption
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(input_path, 'r') as f:
            encrypted_data = f.read()
        
        decrypted_data = decrypt_data(encrypted_data, password)
        if decrypted_data is None:
            return False
        
        with open(output_path, 'w') as f:
            f.write(decrypted_data)
        
        logging.info(f"File decrypted successfully: {input_path} -> {output_path}")
        return True
        
    except Exception as e:
        logging.error(f"File decryption failed: {str(e)}")
        return False

def hash_data(data: str, salt: Optional[bytes] = None) -> tuple:
    """
    Hash data for secure storage
    
    Args:
        data: Data string to hash
        salt: Optional salt bytes
        
    Returns:
        Tuple of (hash, salt)
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    hash_value = kdf.derive(data.encode())
    return base64.urlsafe_b64encode(hash_value).decode(), salt

def verify_hash(data: str, hash_value: str, salt: bytes) -> bool:
    """
    Verify data against stored hash
    
    Args:
        data: Data string to verify
        hash_value: Stored hash value
        salt: Salt bytes used for hashing
        
    Returns:
        True if hash matches, False otherwise
    """
    try:
        computed_hash, _ = hash_data(data, salt)
        return computed_hash == hash_value
        
    except Exception as e:
        logging.error(f"Hash verification failed: {str(e)}")
        return False

def anonymize_text(text: str, patterns: Optional[list] = None) -> str:
    """
    Anonymize text by replacing sensitive patterns
    
    Args:
        text: Text to anonymize
        patterns: List of regex patterns to replace
        
    Returns:
        Anonymized text
    """
    import re
    
    if patterns is None:
        # Default patterns for healthcare data
        patterns = [
            (r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]'),  # Phone numbers
            (r'\b\d{5}\s*\d{5}\b', '[NHS_NUMBER]'),  # NHS numbers
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),  # Email addresses
            (r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '[DATE]'),  # Dates
            (r'\b[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2}\b', '[POSTCODE]'),  # UK postcodes
        ]
    
    anonymized_text = text
    
    for pattern, replacement in patterns:
        anonymized_text = re.sub(pattern, replacement, anonymized_text)
    
    return anonymized_text

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token
    
    Args:
        length: Length of token in bytes
        
    Returns:
        Secure token as base64 string
    """
    try:
        random_bytes = os.urandom(length)
        return base64.urlsafe_b64encode(random_bytes).decode()
        
    except Exception as e:
        logging.error(f"Token generation failed: {str(e)}")
        raise

def secure_compare(a: str, b: str) -> bool:
    """
    Securely compare two strings to prevent timing attacks
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        True if strings match, False otherwise
    """
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    
    return result == 0

class SecureStorage:
    """Secure storage class for sensitive data"""
    
    def __init__(self, password: str):
        """Initialize secure storage with password"""
        self.password = password
        self.fernet = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption key"""
        try:
            key, _ = generate_key(self.password)
            self.fernet = Fernet(key)
        except Exception as e:
            logging.error(f"Failed to initialize encryption: {str(e)}")
            raise
    
    def store(self, key: str, value: str) -> bool:
        """Store encrypted value"""
        try:
            if not self.fernet:
                return False
            
            encrypted_value = self.fernet.encrypt(value.encode())
            # In a real implementation, you'd store this in a secure database
            # For now, we'll just return success
            return True
            
        except Exception as e:
            logging.error(f"Failed to store encrypted value: {str(e)}")
            return False
    
    def retrieve(self, key: str) -> Optional[str]:
        """Retrieve and decrypt value"""
        try:
            if not self.fernet:
                return None
            
            # In a real implementation, you'd retrieve from a secure database
            # For now, we'll just return None
            return None
            
        except Exception as e:
            logging.error(f"Failed to retrieve encrypted value: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete encrypted value"""
        try:
            # In a real implementation, you'd delete from a secure database
            # For now, we'll just return success
            return True
            
        except Exception as e:
            logging.error(f"Failed to delete encrypted value: {str(e)}")
            return False 
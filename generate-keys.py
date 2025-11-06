#!/usr/bin/env python3
"""
Generate Strong API Keys for Production
Run this script to generate secure random keys for .env file
"""

import secrets
import base64

def generate_key(length=48):
    """Generate a cryptographically strong random key"""
    random_bytes = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(random_bytes).decode('utf-8')

def main():
    print("=" * 60)
    print("SECURE API KEY GENERATOR")
    print("=" * 60)
    print()
    
    # Generate API Key
    api_key = generate_key(48)
    print("API_KEY (use in .env):")
    print(f"API_KEY={api_key}")
    print()
    
    # Generate JWT Secret
    jwt_secret = generate_key(48)
    print("JWT_SECRET_KEY (use in .env):")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print()
    
    print("=" * 60)
    print("IMPORTANT:")
    print("=" * 60)
    print("1. Copy these keys to your .env file")
    print("2. Never commit these keys to git")
    print("3. Store securely (password manager, Azure Key Vault)")
    print("4. Share securely with team members only")
    print()
    print("Key Length: 64 characters (384 bits)")
    print("Method: Cryptographically secure random generator")
    print("=" * 60)

if __name__ == "__main__":
    main()

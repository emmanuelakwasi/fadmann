#!/usr/bin/env python3
"""
Generate a secure random secret key for JWT authentication.
Use this to generate your JWT_SECRET_KEY for production.
"""
import secrets

if __name__ == "__main__":
    secret_key = secrets.token_urlsafe(32)
    print("=" * 60)
    print("Generated JWT Secret Key:")
    print("=" * 60)
    print(secret_key)
    print("=" * 60)
    print("\nCopy this value and set it as JWT_SECRET_KEY in your")
    print("Render environment variables or .env file.")
    print("\n⚠️  Keep this secret secure and never commit it to git!")

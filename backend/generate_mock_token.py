"""
Development Helper Script
Generate a mock JWT token for testing APIs without Google OAuth
"""

import jwt
import os
from datetime import datetime, timedelta, timezone
import uuid


def generate_mock_jwt():
    """Generate a mock JWT token for development testing"""

    # Mock user data
    mock_user = {
        "sub": str(uuid.uuid4()),  # User ID
        "email": "test@example.com",
        "name": "Test User",
        "given_name": "Test",
        "family_name": "User",
        "picture": "https://example.com/avatar.jpg",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc),
        "aud": "681563042591-313aq7cma33d1cvlgcu4mv4jtg903l64.apps.googleusercontent.com",
        "iss": "https://accounts.google.com",
    }

    # Use your JWT secret from .env
    jwt_secret = os.getenv(
        "JWT_SECRET_KEY", "dev-jwt-secret-key-change-in-production-123456"
    )

    # Generate token
    token = jwt.encode(mock_user, jwt_secret, algorithm="HS256")

    return token, mock_user


if __name__ == "__main__":
    print("🔧 Development JWT Token Generator")
    print("=" * 50)

    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    token, user_data = generate_mock_jwt()

    print(f"Mock User Data:")
    print(f"  Email: {user_data['email']}")
    print(f"  Name: {user_data['name']}")
    print(f"  User ID: {user_data['sub']}")
    print(f"  Expires: {user_data['exp']}")
    print()

    print("Mock JWT Token (use this in Postman):")
    print("-" * 50)
    print(token)
    print("-" * 50)
    print()

    print("📋 How to use in Postman:")
    print("1. Copy the token above")
    print("2. In Postman, set Authorization to 'Bearer Token'")
    print("3. Paste the token in the Token field")
    print("4. You can now test protected endpoints!")
    print()

    print("🔥 Test this token with:")
    print("POST http://localhost:8000/api/v1/users/auth/google")
    print('{"access_token": "' + token + '"}')

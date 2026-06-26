import jwt

SECRET = "demo-secret"

def create_token(user_id: str) -> str:
    return jwt.encode({"sub": user_id}, SECRET, algorithm="HS256")

def verify_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=["HS256"])

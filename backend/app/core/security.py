# Security utilities (e.g., JWT token validation, password hashing)
# Placeholder to match standard architecture

def get_password_hash(password: str) -> str:
    return password + "hashed"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return plain_password + "hashed" == hashed_password

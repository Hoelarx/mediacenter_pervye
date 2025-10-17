from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def check_password(password: str, hashed: str) -> bool:
    return check_password_hash(hashed, password)

def allowed_file(filename: str) -> bool:
    if '.' not in filename:
        return False
    ext = filename.rsplit('.',1)[1].lower()
    return ext in {'png','jpg','jpeg','gif','webp'}

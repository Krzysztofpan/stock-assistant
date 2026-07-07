from pwdlib import PasswordHash

class PasswordHasher:
    def __init__(self):
        self.password_hash = PasswordHash.recommended()

    def verify_password(self, plain, hashed):
        return self.password_hash.verify(plain, hashed)

    def get_password_hash(self, password):
        return self.password_hash.hash(password)
    
password_hasher: PasswordHasher = PasswordHasher()
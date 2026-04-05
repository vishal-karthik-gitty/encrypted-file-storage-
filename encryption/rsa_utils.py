from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# Generate RSA keys
def generate_keys():
    key = RSA.generate(2048)

    private_key = key
    public_key = key.publickey()

    return public_key, private_key


# Encrypt AES key using RSA
def encrypt_key(aes_key, public_key):
    cipher = PKCS1_OAEP.new(public_key)
    encrypted_key = cipher.encrypt(aes_key)
    return encrypted_key

def decrypt_key(encrypted_key, private_key):
    cipher = PKCS1_OAEP.new(private_key)
    aes_key = cipher.decrypt(encrypted_key)
    return aes_key
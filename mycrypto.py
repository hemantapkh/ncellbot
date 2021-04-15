import hashlib
from base64 import b64encode, b64decode
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.PublicKey import RSA

#: Generate a pair of encrypted privateKey and a publicKey
def generateKeys(passphrase):
    privateKey = RSA.generate(1024)
    publicKey = privateKey.publickey().exportKey().decode()

    #! Encrypting privateKey
    aes = AESCipher(passphrase)
    encryptedPrivateKey = aes.encrypt(privateKey.exportKey().decode())

    return encryptedPrivateKey, publicKey

#: Encryption with RSA using publicKey
def encrypt(text, publicKey):
    publicKey = RSA.importKey(publicKey)
    cipher = PKCS1_OAEP.new(key=publicKey)

    text = text.encode()
    
    #! Encrypt 85 characters at once and separate the cipher text with commas
    chunkSize = 85
    chunkedTexts = [ text[i:i+chunkSize] for i in range(0, len(text), chunkSize) ]

    cipherText = ''

    for i in chunkedTexts:
        cipherText += ',' if cipherText else ''
        cipherText += cipher.encrypt(i).hex()

    return cipherText

#: Decryption with RSA using privateKey
def decrypt(cipherText, privateKey, passphrase):
    #! Decrypting privateKey
    aes = AESCipher(passphrase)
    decryptedPrivateKey = aes.decrypt(privateKey)

    privateKey = RSA.importKey(decryptedPrivateKey)
    decrypt = PKCS1_OAEP.new(key=privateKey)

    #! Split the cipherText with comma to deprypt them individually and concatenate them together
    text = ''
    for i in cipherText.split(','):
        cT = bytes.fromhex(i)
        text+= decrypt.decrypt(cT).decode()

    return text
 
#: Encryption and Decryption with AES-128-CBC
class AESCipher():
    def __init__(self, key):
        self.key = key.encode()
        self.bs = AES.block_size

    def encrypt(self, raw):
        raw = self._pad(raw)
        #! zero based byte[16]
        iv = b'\0'*16
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return b64encode(cipher.encrypt(raw.encode())).decode('UTF-8')

    def decrypt(self, enc):
        enc = b64decode(enc)
        #! zero based byte[16]
        iv = b'\0'*16
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc)).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

#: Generate SHA Hash of a string
def genHash(string):
	result = hashlib.sha512(str(string).encode()) 
	  
	return result.hexdigest()

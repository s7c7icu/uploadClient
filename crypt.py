import zlib
from nacl.secret import SecretBox
import base64
import hashlib

def sha256_hash(data: bytes) -> str:
    """计算给定数据的SHA-256哈希值，并以十六进制字符串形式返回。"""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data)
    return sha256_hash.hexdigest()

def sha512_hash(data: bytes) -> str:
    """计算给定数据的SHA-512哈希值，并以十六进制字符串形式返回。"""
    sha512_hash = hashlib.sha512()
    sha512_hash.update(data)
    return sha512_hash.hexdigest()


# 执行deflate操作的函数
deflate_file = zlib.compress        # (data: bytes) -> bytes

# 执行aes操作的函数
def aes_encrypt(data: bytes, password: str) -> bytes:
    raw_pass = base64.urlsafe_b64decode(password.encode('latin1'))
    key, nonce = (raw_pass[24:], raw_pass[:24])
    return _aes_encrypt(data, key, nonce)


def _aes_encrypt(data: bytes, key: bytes, nonce: bytes) -> bytes:
    return SecretBox(key).encrypt(data, nonce)

# 执行base64操作的函数
base64_encode = base64.b64encode    # (data: bytes) -> bytes
urlsafe_base64_encode = base64.urlsafe_b64encode

def base64_encode_str(data: str, encoding: str = 'utf8') -> str:
    return base64_encode(data.encode(encoding)).decode('ascii')

# 注意：以上函数去掉了async关键字，因为zlib.compress, Fernet.encrypt, 和base64.b64encode
# 都是同步操作。

# 文件加密函数
def encrypt_file(file_content: bytes, password: str, operations: str = "deflate+aes+base64") -> bytes:
    # 默认操作为 "deflate+aes+base64"

    # 根据操作执行文件加密操作
    encrypted_data = file_content
    operations_arr = operations.split("+")
    for operation in operations_arr:
        match operation:
            case "deflate":
                encrypted_data = deflate_file(encrypted_data)
            case "aes":
                encrypted_data = aes_encrypt(encrypted_data, password)
            case "base64":
                encrypted_data = base64_encode(encrypted_data)
            case _:
                print(f"Unsupported operation: {operation}")

    return encrypted_data

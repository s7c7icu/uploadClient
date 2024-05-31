import secrets
import string


def _gen_code(length: int, characters: str) -> str:
    # 使用secrets模块生成指定长度的密码
    return ''.join(secrets.choice(characters) for _ in range(length))


def gen_password(length: int = 16) -> str:
    # 定义密码中可能包含的字符集
    characters = string.ascii_letters + string.digits + "_-"
    return _gen_code(length, characters)


def gen_meta_slug(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return _gen_code(length, characters)


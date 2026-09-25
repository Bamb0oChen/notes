"""Password setup and verification; no plaintext credentials are stored."""
import getpass
import hashlib
import re
import secrets

_PATTERN = re.compile(r'scrypt-v1\$([0-9a-f]{32})\$([0-9a-f]{64})')


def validate_hash(encoded):
    match = _PATTERN.fullmatch(encoded)
    if not match:
        raise ValueError('THOUGHTS_PASSWORD_HASH 格式无效，请使用 passwords.py 重新生成')
    return bytes.fromhex(match[1]), bytes.fromhex(match[2])


def derive(password, salt):
    return hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**17,
                          r=8, p=1, dklen=32, maxmem=256 * 1024 * 1024)


def hash_password(password):
    if not 16 <= len(password) <= 256:
        raise ValueError('管理密码长度须为 16–256 个字符，推荐密码管理器生成的随机密码')
    salt = secrets.token_bytes(16)
    return 'scrypt-v1$' + salt.hex() + '$' + derive(password, salt).hex()


def verify_password(password, encoded):
    salt, expected = validate_hash(encoded)
    return secrets.compare_digest(derive(password, salt), expected)


if __name__ == '__main__':
    password = getpass.getpass('管理密码（至少 16 个字符，不会显示）：')
    again = getpass.getpass('再次输入：')
    if password != again:
        raise SystemExit('两次输入不一致，未生成配置')
    try:
        encoded = hash_password(password)
    except ValueError as error:
        raise SystemExit(str(error))
    # Single quotes prevent Docker Compose from interpolating dollar signs.
    print("\n将下面一行保存到服务器 services/thoughts/.env（不要提交到 Git）：")
    print("THOUGHTS_PASSWORD_HASH='" + encoded + "'")

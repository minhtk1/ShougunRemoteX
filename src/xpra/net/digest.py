# Code copied and adapted from xpra client under GNU General Public License v2.0
# Original inspiration: xpra/xpra/net/digest.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

import os
import hmac
import hashlib
from typing import Sequence


#
# Tính năng: Hàm băm/digest dùng trong quá trình xác thực XPRA
# Mục đích: Cung cấp các phương thức tạo muối (salt) và tạo digest theo thuật toán yêu cầu
# Cách hoạt động:
# - get_salt: sinh bytes ngẫu nhiên dùng làm muối
# - get_digests: trả về danh sách các thuật toán digest hỗ trợ
# - gendigest: tạo digest từ dữ liệu và muối theo thuật toán chỉ định
#


def get_salt(length: int = 32) -> bytes:
    """Sinh muối ngẫu nhiên.

    Args:
        length: Độ dài muối cần sinh (bytes)

    Returns:
        bytes: chuỗi bytes ngẫu nhiên
    """
    if length <= 0 or length > 4096:
        raise ValueError("invalid salt length")
    return os.urandom(length)


def get_digests() -> Sequence[str]:
    """Danh sách thuật toán digest hỗ trợ.

    Trả về các thuật toán thường dùng trong xpra: XOR (kết hợp muối),
    các hàm băm hashlib và HMAC-SHA1.
    """
    return (
        "xor",
        "md5",
        "sha1",
        "sha224",
        "sha256",
        "sha384",
        "sha512",
        "hmac",
        # "des" không khuyến nghị; server cũ có thể yêu cầu nhưng sẽ bị chặn ở nơi khác
    )


def _xor_bytes(a: bytes, b: bytes) -> bytes:
    """XOR 2 chuỗi bytes theo độ dài nhỏ nhất giữa chúng."""
    size = min(len(a), len(b))
    return bytes(x ^ y for x, y in zip(a[:size], b[:size]))


def gendigest(name: str, data, salt) -> bytes:
    """Sinh digest theo tên thuật toán.

    Args:
        name: tên thuật toán (vd: 'xor', 'md5', 'sha256', 'sha512', 'hmac')
        data: dữ liệu đầu vào (mật khẩu hoặc muối client), str hoặc bytes
        salt: muối (server salt hoặc muối kết hợp), str hoặc bytes

    Returns:
        bytes: kết quả digest
    """
    if isinstance(data, str):
        data_bytes = data.encode("utf-8", "ignore")
    else:
        data_bytes = bytes(data)
    if isinstance(salt, str):
        salt_bytes = salt.encode("utf-8", "ignore")
    else:
        salt_bytes = bytes(salt)

    algo = (name or "").lower()

    # "xor": dùng để kết hợp 2 muối (client/server)
    if algo == "xor":
        return _xor_bytes(data_bytes, salt_bytes)

    # "hmac": Sử dụng HMAC-SHA1 theo truyền thống của xpra
    if algo == "hmac":
        return hmac.new(data_bytes, salt_bytes, hashlib.sha1).digest()

    # Các hàm băm hashlib: md5/sha1/sha224/sha256/sha384/sha512
    if algo in {"md5", "sha1", "sha224", "sha256", "sha384", "sha512"}:
        hasher = hashlib.new(algo)
        # Quy ước: băm data + salt
        # (đối xứng với server vì chỉ phụ thuộc thứ tự nhất quán)
        hasher.update(data_bytes)
        hasher.update(salt_bytes)
        return hasher.digest()

    # Thuật toán không hỗ trợ
    return b""



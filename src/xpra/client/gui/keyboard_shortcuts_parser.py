# This file is part of ShougunRemoteX-Python project
# Minimal keyboard shortcuts parser compatible with Xpra client expectations
# License: GNU General Public License v2.0

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple


# Tính năng: Parser phím tắt tối giản cho client Xpra
# Mục đích: Tránh lỗi ModuleNotFoundError khi import parser gốc của Xpra
# Cách hoạt động: Cung cấp 3 hàm API mà client gọi tới với xử lý cơ bản, an toàn


def get_modifier_names(mod_meanings: Dict[str, str] | None) -> Dict[str, str]:
    """Trả về mapping tên chuẩn hóa của modifier.

    - Đầu vào từ `Keyboard.get_keymap_modifiers()` thường là map meaning -> modX
      Ví dụ: {"Meta_L": "mod1", "ISO_Level3_Shift": "mod5", ...}
    - Hàm này chuẩn hóa ra các key thường dùng (lowercase) để tra cứu nhanh.
    """
    # Mapping mặc định các modifier phổ biến
    mapping: Dict[str, str] = {
        "shift": "shift",
        "control": "control",
        "ctrl": "control",
        "alt": "alt",
        "meta": "meta",
        "super": "super",
        "caps_lock": "caps_lock",
        "num_lock": "num_lock",
        "mod1": "mod1",
        "mod2": "mod2",
        "mod3": "mod3",
        "mod4": "mod4",
        "mod5": "mod5",
    }

    # Bổ sung từ mod_meanings (nếu có) để hỗ trợ các tên meaning khác
    if mod_meanings:
        for meaning, mod in mod_meanings.items():
            key = (meaning or "").strip().lower()
            val = (mod or "").strip().lower()
            if key and val:
                mapping[key] = val
    return mapping


def parse_shortcut_modifiers(shortcut_modifiers: str | Sequence[str], modifier_names: Dict[str, str]) -> List[str]:
    """Phân tích danh sách modifier cho phím tắt.

    - Cho phép truyền vào dạng chuỗi "ctrl+alt" hoặc list ["ctrl", "alt"].
    - Trả về list các tên modifier chuẩn hóa (lowercase).
    - Nếu là "auto" hoặc rỗng thì trả về list rỗng (không ép buộc modifier).
    """
    if not shortcut_modifiers or (isinstance(shortcut_modifiers, str) and shortcut_modifiers.strip().lower() == "auto"):
        return []

    items: Iterable[str]
    if isinstance(shortcut_modifiers, str):
        items = (x.strip() for x in shortcut_modifiers.replace("+", ",").split(","))
    else:
        items = (str(x).strip() for x in shortcut_modifiers)

    normalized: List[str] = []
    for it in items:
        if not it:
            continue
        key = it.lower()
        normalized.append(modifier_names.get(key, key))
    return normalized


def parse_shortcuts(
    key_shortcuts: Sequence[str] | Sequence[Tuple[Sequence[str], str, Sequence]] | None,
    shortcut_modifiers: Sequence[str],
    modifier_names: Dict[str, str],
) -> Dict[str, List[Tuple[List[str], str, Tuple]]]:
    """Phân tích cấu hình phím tắt thành cấu trúc mà `KeyboardHelper` mong đợi.

    Trả về dict:
        { key_name: [ (required_modifiers, action_name, action_args), ... ] }

    Ghi chú: Ở đây triển khai tối giản để an toàn:
      - Nếu không có cấu hình, trả về dict rỗng.
      - Nếu phần tử đã ở dạng tuple (mods, action, args) thì giữ nguyên với chuẩn hóa mods.
      - Với cấu hình dạng chuỗi đơn giản "Ctrl+Alt+F11:toggle_fullscreen" sẽ được parse cơ bản.
    """
    result: Dict[str, List[Tuple[List[str], str, Tuple]]] = {}
    if not key_shortcuts:
        return result

    def add_shortcut(key_name: str, mods: Sequence[str], action: str, args: Sequence | None = None) -> None:
        key = (key_name or "").strip()
        if not key:
            return
        norm_mods = [modifier_names.get(m.lower(), m.lower()) for m in mods]
        lst = result.setdefault(key, [])
        lst.append((norm_mods, action, tuple(args or ())))

    for entry in key_shortcuts:
        # Hỗ trợ dạng đã chuẩn: (mods, action, args), key sẽ được xác định bởi action sau này
        if isinstance(entry, tuple) and len(entry) == 3 and isinstance(entry[0], (list, tuple)):
            # Không biết key đích, bỏ qua để tránh sai logic
            # (phiên bản tối giản này chỉ hỗ trợ format string cấu hình)
            continue

        # Hỗ trợ dạng chuỗi: "Ctrl+Alt+F11:toggle_fullscreen()" hoặc "Shift+F10:menu_open"
        s = str(entry).strip()
        if not s:
            continue
        try:
            parts = s.split(":", 1)
            left = parts[0]
            right = parts[1] if len(parts) > 1 else "pass"
            lr = [x.strip() for x in left.replace(" ", "").split("+") if x.strip()]
            if not lr:
                continue
            # Phần cuối bên trái mặc định là key_name, các phần trước là modifiers
            key_name = lr[-1]
            mods = lr[:-1]
            # Kết hợp với shortcut_modifiers mặc định (nếu có)
            mods = list(shortcut_modifiers) + mods

            # Phân tích action và args: ví dụ "toggle_fullscreen()", "do_something(1,2)"
            action = right
            args: Tuple = ()
            if "(" in right and right.endswith(")"):
                fname, argstr = right.split("(", 1)
                action = fname.strip() or "pass"
                argstr = argstr[:-1].strip()  # bỏ dấu )
                if argstr:
                    args = tuple(x.strip() for x in argstr.split(",") if x.strip())
            else:
                action = (right or "pass").strip()

            add_shortcut(key_name, mods, action, args)
        except Exception:
            # Parser tối giản: nếu lỗi cú pháp thì bỏ qua entry đó để an toàn
            continue

    return result




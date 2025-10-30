# This file is part of Xpra.
# Copyright (C) 2010 Nathaniel Smith <njs@pobox.com>
# Copyright (C) 2011 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.


def get_backends() -> list[type]:
    from xpra.platform.win32.tray import Win32Tray
    return [Win32Tray]


def get_forwarding_backends(*_args) -> list[type]:
    return get_backends()

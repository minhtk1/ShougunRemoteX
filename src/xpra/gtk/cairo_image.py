# Code copied from xpra-minhtk under GNU General Public License v2.0
# Original source: xpra-minhtk/xpra/gtk/cairo_image.pyx (Python implementation)
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

# Python implementation fallback for cairo_image.pyx
# Note: This is a simplified version. For full performance, use the Cython version.

from typing import Dict
from collections.abc import Sequence
from cairo import ImageSurface, FORMAT_ARGB32, FORMAT_RGB24, FORMAT_RGB16_565, FORMAT_RGB30

CAIRO_FORMAT: Dict[int, str] = {
    0: "Invalid",
    1: "ARGB32",
    2: "RGB24",
    3: "A8",
    4: "A1",
    5: "RGB16_565",
    6: "RGB30",
}

CAIRO_FORMATS: Dict[int, Sequence[str]] = {
    FORMAT_RGB24: ("RGB", "RGBX", "BGR", "BGRX", "RGBA", "BGRA"),
    FORMAT_ARGB32: ("BGRX", "BGRA", "RGBA", "RGBX"),
    FORMAT_RGB16_565: ("BGR565",),
    FORMAT_RGB30: ("r210",),
}


def make_image_surface(fmt, rgb_format: str, pixels, width: int, height: int, stride: int) -> ImageSurface:
    """
    Tạo ImageSurface từ pixel data.
    Đây là implementation Python đơn giản, không hiệu quả bằng Cython version.
    """
    if len(pixels) < height * stride:
        raise ValueError(
            f"pixel buffer is too small for {width}x{height} with stride={stride}: "
            f"only {len(pixels)} bytes, expected {height*stride}"
        )

    # Tạo surface mới
    image_surface = ImageSurface(fmt, width, height)

    # Lấy pixel data từ surface
    surface_stride = image_surface.get_stride()
    surface_data = image_surface.get_data()

    # Convert pixel data dựa trên format
    if fmt == FORMAT_RGB24:
        if rgb_format == "BGR":
            # Copy và convert BGR -> RGB24
            for y in range(height):
                for x in range(width):
                    src_idx = x * 3 + y * stride
                    dst_idx = x * 4 + y * surface_stride
                    if src_idx + 2 < len(pixels) and dst_idx + 3 < len(surface_data):
                        surface_data[dst_idx + 0] = pixels[src_idx + 0]  # B
                        surface_data[dst_idx + 1] = pixels[src_idx + 1]  # G
                        surface_data[dst_idx + 2] = pixels[src_idx + 2]  # R
                        surface_data[dst_idx + 3] = 0xFF  # X
        elif rgb_format == "RGB":
            for y in range(height):
                for x in range(width):
                    src_idx = x * 3 + y * stride
                    dst_idx = x * 4 + y * surface_stride
                    if src_idx + 2 < len(pixels) and dst_idx + 3 < len(surface_data):
                        surface_data[dst_idx + 0] = pixels[src_idx + 2]  # B
                        surface_data[dst_idx + 1] = pixels[src_idx + 1]  # G
                        surface_data[dst_idx + 2] = pixels[src_idx + 0]  # R
                        surface_data[dst_idx + 3] = 0xFF  # X
        elif rgb_format in ("BGRX", "BGRA"):
            # Direct copy với stride adjustment
            for y in range(height):
                copy_len = min(stride, surface_stride)
                src_start = y * stride
                dst_start = y * surface_stride
                if src_start + copy_len <= len(pixels) and dst_start + copy_len <= len(surface_data):
                    surface_data[dst_start:dst_start + copy_len] = pixels[src_start:src_start + copy_len]
        elif rgb_format in ("RGBX", "RGBA"):
            for y in range(height):
                for x in range(width):
                    src_idx = x * 4 + y * stride
                    dst_idx = x * 4 + y * surface_stride
                    if src_idx + 3 < len(pixels) and dst_idx + 3 < len(surface_data):
                        surface_data[dst_idx + 0] = pixels[src_idx + 2]  # B
                        surface_data[dst_idx + 1] = pixels[src_idx + 1]  # G
                        surface_data[dst_idx + 2] = pixels[src_idx + 0]  # R
                        surface_data[dst_idx + 3] = 0xFF  # X
        else:
            raise ValueError(f"unhandled pixel format for RGB24: {rgb_format!r}")
    elif fmt == FORMAT_ARGB32:
        if rgb_format == "BGRA":
            # Direct copy
            for y in range(height):
                copy_len = min(stride, surface_stride)
                src_start = y * stride
                dst_start = y * surface_stride
                if src_start + copy_len <= len(pixels) and dst_start + copy_len <= len(surface_data):
                    surface_data[dst_start:dst_start + copy_len] = pixels[src_start:src_start + copy_len]
        elif rgb_format == "RGBA":
            for y in range(height):
                for x in range(width):
                    src_idx = x * 4 + y * stride
                    dst_idx = x * 4 + y * surface_stride
                    if src_idx + 3 < len(pixels) and dst_idx + 3 < len(surface_data):
                        surface_data[dst_idx + 0] = pixels[src_idx + 2]  # B
                        surface_data[dst_idx + 1] = pixels[src_idx + 1]  # G
                        surface_data[dst_idx + 2] = pixels[src_idx + 0]  # R
                        surface_data[dst_idx + 3] = pixels[src_idx + 3]  # A
        elif rgb_format in ("RGBX", "BGRX", "RGB", "BGR"):
            # Similar conversions as above
            for y in range(height):
                for x in range(width):
                    if rgb_format in ("RGBX", "BGRX"):
                        src_idx = x * 4 + y * stride
                    else:
                        src_idx = x * 3 + y * stride
                    dst_idx = x * 4 + y * surface_stride
                    if src_idx < len(pixels) and dst_idx + 3 < len(surface_data):
                        if rgb_format == "RGBX":
                            surface_data[dst_idx + 0] = pixels[src_idx + 2]  # B
                            surface_data[dst_idx + 1] = pixels[src_idx + 1]  # G
                            surface_data[dst_idx + 2] = pixels[src_idx + 0]  # R
                            surface_data[dst_idx + 3] = 0xFF  # A
                        elif rgb_format == "BGRX":
                            surface_data[dst_idx + 0] = pixels[src_idx + 0]  # B
                            surface_data[dst_idx + 1] = pixels[src_idx + 1]  # G
                            surface_data[dst_idx + 2] = pixels[src_idx + 2]  # R
                            surface_data[dst_idx + 3] = 0xFF  # A
                        elif rgb_format == "RGB":
                            surface_data[dst_idx + 0] = pixels[src_idx + 2]  # B
                            surface_data[dst_idx + 1] = pixels[src_idx + 1]  # G
                            surface_data[dst_idx + 2] = pixels[src_idx + 0]  # R
                            surface_data[dst_idx + 3] = 0xFF  # A
                        elif rgb_format == "BGR":
                            surface_data[dst_idx + 0] = pixels[src_idx + 0]  # B
                            surface_data[dst_idx + 1] = pixels[src_idx + 1]  # G
                            surface_data[dst_idx + 2] = pixels[src_idx + 2]  # R
                            surface_data[dst_idx + 3] = 0xFF  # A
        else:
            raise ValueError(f"unhandled pixel format for ARGB32: {rgb_format!r}")
    elif fmt == FORMAT_RGB30:
        if rgb_format == "r210":
            # Direct copy
            for y in range(height):
                copy_len = min(stride, surface_stride)
                src_start = y * stride
                dst_start = y * surface_stride
                if src_start + copy_len <= len(pixels) and dst_start + copy_len <= len(surface_data):
                    surface_data[dst_start:dst_start + copy_len] = pixels[src_start:src_start + copy_len]
        else:
            raise ValueError(f"unhandled pixel format for RGB30 {rgb_format!r}")
    elif fmt == FORMAT_RGB16_565:
        if rgb_format == "BGR565":
            # Direct copy
            for y in range(height):
                copy_len = min(stride, surface_stride)
                src_start = y * stride
                dst_start = y * surface_stride
                if src_start + copy_len <= len(pixels) and dst_start + copy_len <= len(surface_data):
                    surface_data[dst_start:dst_start + copy_len] = pixels[src_start:src_start + copy_len]
        else:
            raise ValueError(f"unhandled pixel format for RGB16_565 {rgb_format!r}")
    else:
        raise ValueError(f"unhandled cairo format {fmt!r}")

    image_surface.mark_dirty()
    return image_surface


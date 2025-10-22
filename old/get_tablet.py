import struct, sys, json

def bmp_palette_raw(path):
    with open(path, "rb") as f:
        d = f.read()

    if d[:2] != b"BM":
        raise ValueError("Не BMP (нет сигнатуры BM)")

    bfSize, bfReserved1, bfReserved2, bfOffBits = struct.unpack_from("<IHHI", d, 2)
    dib_size = struct.unpack_from("<I", d, 14)[0]

    # Поддержим BITMAPINFOHEADER (40+) и OS/2 V1 (12)
    os2_v1 = (dib_size == 12)
    if os2_v1:
        # OS/2 V1
        biWidth, biHeight, biPlanes, biBitCount = struct.unpack_from("<HHHH", d, 14+4)
        biCompression = 0
        biClrUsed = 0
        header_end = 14 + dib_size
    else:
        (biSize, biWidth, biHeight, biPlanes, biBitCount, biCompression,
         biSizeImage, biXPelsPerMeter, biYPelsPerMeter,
         biClrUsed, biClrImportant) = struct.unpack_from("<IiiHHIIiiII", d, 14)
        header_end = 14 + biSize

    palette_entries = 0
    if biBitCount in (1, 4, 8):
        palette_entries = biClrUsed if biClrUsed else (1 << biBitCount)
    entry_size = 3 if os2_v1 else 4

    palette = []
    if palette_entries:
        base = header_end
        for i in range(palette_entries):
            b = d[base + i*entry_size + 0]
            g = d[base + i*entry_size + 1]
            r = d[base + i*entry_size + 2]
            palette.append((r, g, b))

    return {
        "bit_count": biBitCount,
        "biClrUsed": biClrUsed if not os2_v1 else 0,
        "palette_len": len(palette),
        "palette": palette
    }

if __name__ == "__main__":
    path = "pal8rletrns.bmp"
    result = bmp_palette_raw(path)
    print(result)

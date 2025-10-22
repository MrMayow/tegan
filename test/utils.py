from PIL import Image
from typing import List, Tuple

def _get_palette_rgb(img):
    pal = img.getpalette()[:256*3]
    return [(pal[i], pal[i+1], pal[i+2]) for i in range(0, len(pal), 3)]

def _weight(rgb):
    r,g,b = rgb
    return (r<<16) + (g<<8) + b

def _build_sorted_tables(palette):
    indexed = list(enumerate(palette))
    indexed.sort(key=lambda x: _weight(x[1]))
    orig_to_pos = {orig:i for i,(orig,_) in enumerate(indexed)}
    pos_to_orig = {i:orig for i,(orig,_) in enumerate(indexed)}
    return indexed, orig_to_pos, pos_to_orig



def _nearest_pos_with_lsb(target_bit, pos, n):
    if (pos & 1) == target_bit:
        return pos
    r = 1
    while True:
        dn = pos - r
        up = pos + r
        cand = []
        if dn >= 0 and ((dn & 1) == target_bit):
            cand.append(dn)
        if up < n and ((up & 1) == target_bit):
            cand.append(up)
        if cand:
            return min(cand, key=lambda c: abs(c - pos))
        if dn < 0 and up >= n:
            return pos
        r += 1

def embed_palette_lsb_nohdr(src_path: str, dst_path: str, payload: bytes):
    img = Image.open(src_path).convert("P")
    palette = _get_palette_rgb(img)
    _, orig_to_pos, pos_to_orig = _build_sorted_tables(palette)
    w, h = img.size
    pixels = img.load()

    # полезная нагрузка -> биты MSB→LSB
    bits: List[int] = []
    for b in payload:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)

    capacity = w * h
    if len(bits) > capacity:
        raise ValueError(f"Недостаточная емкость: нужно {len(bits)} бит, есть {capacity}")

    n = 256
    k = 0
    for y in range(h):
        for x in range(w):
            if k >= len(bits): break
            orig_idx = pixels[x, y]
            pos = orig_to_pos[orig_idx]
            target = bits[k]
            new_pos = _nearest_pos_with_lsb(target, pos, n)
            print("pos:", pos)
            print("new_pos:", new_pos)
            print("-------------------------")
            pixels[x, y] = pos_to_orig[new_pos]
            k += 1
        if k >= len(bits): break
    img.save(dst_path)

def extract_palette_lsb_nohdr(stego_path: str, bit_len: int) -> bytes:
    img = Image.open(stego_path).convert("P")
    palette = _get_palette_rgb(img)
    _, orig_to_pos, _ = _build_sorted_tables(palette)
    w, h = img.size
    pixels = img.load()

    bits: List[int] = []
    need = bit_len
    for y in range(h):
        for x in range(w):
            if len(bits) >= need: break
            pos = orig_to_pos[pixels[x, y]]
            bits.append(pos & 1)
        if len(bits) >= need: break

    out = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8: break
        v = 0
        for b in chunk:  # MSB→LSB
            v = (v << 1) | b
        out.append(v)
    return bytes(out)

from PIL import Image
from typing import List, Tuple
import math

def get_palette_rgb(img):
    pal = img.getpalette()[:256*3]
    return [(pal[i], pal[i+1], pal[i+2]) for i in range(0, len(pal), 3)]

def rgb_to_lab(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
    g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
    b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    x /= 0.95047
    z /= 1.08883
    def f(t):
        return t ** (1/3) if t > 0.008856 else (7.787 * t) + (16 / 116)
    fx, fy, fz = f(x), f(y), f(z)
    L = (116 * fy) - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return (L, a, b)

def color_distance(rgb1, rgb2):
    lab1 = rgb_to_lab(rgb1)
    lab2 = rgb_to_lab(rgb2)
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))

def weight(rgb):
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b

def build_sorted_tables(palette):
    indexed = list(enumerate(palette))
    indexed.sort(key=lambda x: weight(x[1]))
    orig_to_pos = {orig: i for i, (orig, _) in enumerate(indexed)}
    pos_to_orig = {i: orig for i, (orig, _) in enumerate(indexed)}
    return indexed, orig_to_pos, pos_to_orig

def find_nearest_color_with_lsb(target_bit, orig_idx, palette, orig_to_pos):
    orig_color = palette[orig_idx]
    n = len(palette)
    candidates = []
    for idx in range(n):
        pos = orig_to_pos[idx]
        if (pos & 1) == target_bit:
            dist = color_distance(orig_color, palette[idx])
            candidates.append((dist, idx))
    
    if not candidates:
        return orig_idx

    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]

def embed_palette_lsb_nohdr(src_path: str, dst_path: str, payload: bytes):
    img = Image.open(src_path).convert("P")
    palette = get_palette_rgb(img)
    
    aaa, orig_to_pos, pos_to_orig = build_sorted_tables(palette)
    for i in aaa:
        print(i[0], ":", i[1])
    w, h = img.size
    pixels = img.load()
    
    bits: List[int] = []
    for b in payload:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    capacity = w * h
    if len(bits) > capacity:
        raise ValueError(f"Недостаточная емкость: нужно {len(bits)} бит, есть {capacity}")
    k = 0
    for y in range(h):
        for x in range(w):
            
            if k >= len(bits):
                break
            orig_idx = pixels[x, y]
            target = bits[k]
            new_idx = find_nearest_color_with_lsb(target, orig_idx, palette, orig_to_pos)
            pixels[x, y] = new_idx
            k += 1
        if k >= len(bits):
            break
    img.save(dst_path)

def extract_palette_lsb_nohdr(stego_path: str, bit_len: int) -> bytes:
    img = Image.open(stego_path).convert("P")
    palette = get_palette_rgb(img)
    _, orig_to_pos, _ = build_sorted_tables(palette)

    w, h = img.size
    pixels = img.load()
    bits: List[int] = []
    need = bit_len
    for y in range(h):
        for x in range(w):
            if len(bits) >= need:
                break
            pos = orig_to_pos[pixels[x, y]]
            bits.append(pos & 1)
        if len(bits) >= need:
            break
    out = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            break
        v = 0
        for b in chunk:
            v = (v << 1) | b
        out.append(v)
    
    return bytes(out)

secret_string = "Зовут его Николаем Петровичем Кирсановым. У него в пятнадцати верстах от постоялого дворика хорошее имение в двести душ, или, как он выражается с тех пор, как размежевался с крестьянами и завел «ферму», — в две тысячи десятин земли. Отец его, боевой генерал 1812 года, полуграмотный, грубый, но не злой русский человек, всю жизнь свою тянул лямку, командовал сперва бригадой, потом дивизией и постоянно жил в провинции, где в силу своего чина играл довольно значительную роль. Николай Петрович родился на юге России, подобно старшему своему брату Павлу, о котором речь впереди, и воспитывался до четырнадцатилетнего возраста дома, окруженный дешевыми гувернерами, развязными, но подобострастными адъютантами и прочими полковыми и штабными личностями. "
secret_bytes = bytes(secret_string, encoding='utf-8')
embed_palette_lsb_nohdr("source.bmp", "stego_full.bmp", secret_bytes)
restored_bytes = extract_palette_lsb_nohdr("stego_full.bmp", len(secret_bytes)*8)
restored_string = restored_bytes.decode('utf-8')
print(restored_string, restored_string == secret_string)
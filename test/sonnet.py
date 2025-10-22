from PIL import Image
from typing import List, Tuple
import math

def _get_palette_rgb(img):
    pal = img.getpalette()[:256*3]
    return [(pal[i], pal[i+1], pal[i+2]) for i in range(0, len(pal), 3)]

def _rgb_to_lab(rgb):
    """Конвертация RGB в LAB для перцептивного сравнения цветов"""
    r, g, b = [x / 255.0 for x in rgb]
    
    # Gamma correction
    r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
    g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
    b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92
    
    # RGB to XYZ
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    
    # XYZ to LAB
    x /= 0.95047
    z /= 1.08883
    
    def f(t):
        return t ** (1/3) if t > 0.008856 else (7.787 * t) + (16 / 116)
    
    fx, fy, fz = f(x), f(y), f(z)
    
    L = (116 * fy) - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    
    return (L, a, b)

def _color_distance(rgb1, rgb2):
    """Вычисляет перцептивное расстояние между цветами в LAB пространстве"""
    lab1 = _rgb_to_lab(rgb1)
    lab2 = _rgb_to_lab(rgb2)
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))

def _weight(rgb):
    """Перцептивная яркость для сортировки"""
    r, g, b = rgb
    # Weighted luminance
    return 0.299 * r + 0.587 * g + 0.114 * b

def _build_sorted_tables(palette):
    indexed = list(enumerate(palette))
    # Сортировка по перцептивной яркости, а не по побитовому весу
    indexed.sort(key=lambda x: _weight(x[1]))
    
    orig_to_pos = {orig: i for i, (orig, _) in enumerate(indexed)}
    pos_to_orig = {i: orig for i, (orig, _) in enumerate(indexed)}
    
    return indexed, orig_to_pos, pos_to_orig

def _find_nearest_color_with_lsb(target_bit, orig_idx, palette, orig_to_pos):
    """
    Находит ближайший цвет с нужным LSB, используя перцептивное расстояние
    """
    orig_color = palette[orig_idx]
    n = len(palette)
    
    # Создаём список кандидатов с нужным LSB
    candidates = []
    for idx in range(n):
        pos = orig_to_pos[idx]
        if (pos & 1) == target_bit:
            dist = _color_distance(orig_color, palette[idx])
            candidates.append((dist, idx))
    
    if not candidates:
        return orig_idx
    
    # Возвращаем цвет с минимальным перцептивным расстоянием
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]

def embed_palette_lsb_nohdr(src_path: str, dst_path: str, payload: bytes):
    img = Image.open(src_path).convert("P")
    palette = _get_palette_rgb(img)
    
    _, orig_to_pos, pos_to_orig = _build_sorted_tables(palette)
    
    w, h = img.size
    pixels = img.load()
    
    # Полезная нагрузка -> биты MSB→LSB
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
            
            # Используем перцептивный поиск ближайшего цвета
            new_idx = _find_nearest_color_with_lsb(target, orig_idx, palette, orig_to_pos)
            pixels[x, y] = new_idx
            
            k += 1
        if k >= len(bits):
            break
    
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
        for b in chunk:  # MSB→LSB
            v = (v << 1) | b
        out.append(v)
    
    return bytes(out)


secret = b"Hello my fdfksdfjsdlkfsdjfslk;dfjslkddfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjffjlksdjf;lksdjfklsjdflksjdflksjdfjsdkjgj5rtjgohdfogdfjgodfigj"
embed_palette_lsb_nohdr("cat.bmp", "stego.bmp", secret)
restored = extract_palette_lsb_nohdr("stego.bmp", len(secret)*8)
print(restored, restored == secret)
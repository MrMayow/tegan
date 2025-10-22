from PIL import Image
from typing import List, Tuple, Dict
import math

def _get_palette_rgb(img: Image.Image) -> List[Tuple[int, int, int]]:
    """Извлекает палитру как список RGB-кортежей (до 256 цветов)."""
    pal = img.getpalette()[:256*3]  # Получаем байты палитры
    return [(pal[i], pal[i+1], pal[i+2]) for i in range(0, len(pal), 3)]

def _build_sorted_tables(palette: List[Tuple[int, int, int]]) -> Tuple[List[Tuple[int, Tuple[int, int, int]]], Dict[int, int], Dict[int, int]]:
    """Строит отсортированные таблицы: по визуальной яркости (L2-подобная), orig_to_pos, pos_to_orig."""
    # Сортировка по grayscale яркости для минимальных визуальных сдвигов: 0.299R + 0.587G + 0.114B
    indexed = list(enumerate(palette))
    indexed.sort(key=lambda x: 0.299 * x[1][0] + 0.587 * x[1][1] + 0.114 * x[1][2])
    
    orig_to_pos = {orig_i: new_i for new_i, (orig_i, _) in enumerate(indexed)}
    pos_to_orig = {new_i: orig_i for new_i, (orig_i, _) in enumerate(indexed)}
    return indexed, orig_to_pos, pos_to_orig

def _nearest_pos_with_lsb(target_bit: int, pos_to_orig: Dict[int, int], pos: int, n: int) -> int:
    """Находит ближайшую позицию в отсортированной палитре с нужным LSB (target_bit), отличающуюся max на 1."""
    if pos >= n:
        return pos  # Ошибка, но возвращаем оригинал
    
    # Проверяем только pos и pos+1 (LSB 0 или 1)
    candidates = []
    for delta in [0, 1]:  # Только минимальные изменения
        new_pos = pos + delta
        if 0 <= new_pos < n and (new_pos & 1) == target_bit:  # LSB совпадает
            candidates.append(new_pos)
    
    if candidates:
        return min(candidates, key=lambda c: abs(c - pos))  # Ближайшая по позиции (минимальный сдвиг)
    return pos  # Если нет, не меняем — избежим искажений

def embed_palette_lsb_no_hdr(src_path: str, dst_path: str, payload: bytes) -> None:
    """Встраивает payload (байты) в палитру LSB: 1 бит на пиксель, без заголовка."""
    if not payload:
        raise ValueError("Payload пустой")
    
    img = Image.open(src_path).convert("P", palette=Image.ADAPTIVE, colors=256)  # Adaptive для цветных изображений
    palette = _get_palette_rgb(img)
    sorted_palette, orig_to_pos, pos_to_orig = _build_sorted_tables(palette)
    w, h = img.size
    pixels = img.load()
    
    # Конвертируем payload в биты (1 бит на пиксель, MSB first)
    bits: List[int] = []
    for byte in payload:
        for i in range(7, -1, -1):  # 8 битов на байт
            bits.append((byte >> i) & 1)
    
    capacity = w * h  # 1 бит на пиксель
    if len(bits) > capacity:
        raise ValueError(f"Payload слишком большой: {len(bits)} битов > {capacity}")
    
    n = 256
    k = 0
    for y in range(h):
        if k >= len(bits):
            break
        for x in range(w):
            if k >= len(bits):
                break
            orig_idx = pixels[x, y]
            pos = orig_to_pos.get(orig_idx, orig_idx)
            target = bits[k]
            new_pos = _nearest_pos_with_lsb(target, pos_to_orig, pos, n)
            if new_pos != pos:  # Меняем только если нужно
                pixels[x, y] = pos_to_orig[new_pos]  # Возвращаем оригинальный индекс новой позиции
            k += 1
    
    # Сохраняем с оригинальной палитрой (не меняем её)
    img.putpalette(img.getpalette())  # Фиксируем палитру
    img.save(dst_path, optimize=False)  # Без оптимизации, чтобы пиксели сохранились

def extract_palette_lsb_no_hdr(stego_path: str, bit_len: int) -> bytes:
    """Извлекает bit_len битов из LSB палитры и возвращает как байты."""
    img = Image.open(stego_path).convert("P")
    palette = _get_palette_rgb(img)
    sorted_palette, orig_to_pos, pos_to_orig = _build_sorted_tables(palette)  # Та же сортировка
    w, h = img.size
    pixels = img.load()
    
    bits: List[int] = []
    need = bit_len
    for y in range(h):
        if len(bits) >= need:
            break
        for x in range(w):
            if len(bits) >= need:
                break
            orig_idx = pixels[x, y]
            pos = orig_to_pos.get(orig_idx, orig_idx)
            bits.append(pos & 1)  # LSB позиции
    
    if len(bits) < bit_len:
        raise ValueError(f"Недостаточно битов: {len(bits)} < {bit_len}")
    
    # Конвертируем биты в байты (MSB first)
    out = bytearray()
    for i in range(0, bit_len, 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            break
        v = 0
        for b in chunk:
            v = (v << 1) | b
        out.append(v)
    return bytes(out)

secret = b"Hello my fdfksdfjsdlkfsdjfslk;dfjslkddfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjffjlksdjf;lksdjfklsjdflksjdflksjdfjsdkjgj5rtjgohdfogdfjgodfigj"
embed_palette_lsb_no_hdr("cat.bmp", "stego.bmp", secret)
restored = extract_palette_lsb_no_hdr("stego.bmp", len(secret)*8)
print(restored, restored == secret)
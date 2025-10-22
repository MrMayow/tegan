from PIL import Image
from typing import List, Tuple
import math

def _get_palette_rgb(img: Image.Image) -> List[Tuple[int,int,int]]:
    assert img.mode == "P", "Нужно палитровое изображение 8 bpp"
    pal = img.getpalette()  # flat list [R0,G0,B0, R1,G1,B1, ...]
    # ограничим 256*3 элементов
    pal = pal[:256*3]
    return [(pal[i], pal[i+1], pal[i+2]) for i in range(0, len(pal), 3)]

def _weight(rgb: Tuple[int,int,int]) -> int:
    r,g,b = rgb
    return (r<<16) + (g<<8) + b  # W = 65536*R + 256*G + B

def _build_sorted_tables(palette: List[Tuple[int,int,int]]):
    # Tsort: список кортежей (orig_index, rgb) отсортированный по W
    indexed = list(enumerate(palette))
    indexed.sort(key=lambda x: _weight(x[1]))
    # отображения
    orig_to_pos = {orig:i for i,(orig,_) in enumerate(indexed)}
    pos_to_orig = {i:orig for i,(orig,_) in enumerate(indexed)}
    return indexed, orig_to_pos, pos_to_orig

def _nearest_pos_with_lsb(target_bit: int, pos: int, n: int) -> int:
    # Если НЗБ(pos) совпадает — оставляем, иначе ищем ближайший индекс
    if (pos & 1) == target_bit:
        return pos
    # двунаправленный поиск с увеличением радиуса
    radius = 1
    best = None
    while True:
        down = pos - radius
        up = pos + radius
        cand = []
        if down >= 0 and ((down & 1) == target_bit):
            cand.append(down)
        if up < n and ((up & 1) == target_bit):
            cand.append(up)
        if cand:
            # выбрать ближайший (по |delta|)
            best = min(cand, key=lambda c: abs(c - pos))
            return best
        radius += 1
        if down < 0 and up >= n:
            # не найдено — возвращаем pos (не должно случаться при n>=2)
            return pos

def embed_palette_lsb(
    src_path: str,
    dst_path: str,
    bitstream: bytes,
    use_header_len: bool = True
):
    """
    Встраивает битовый поток в индексы 8-bit палитрового изображения.
    По умолчанию пишет 32-битный заголовок длины (в битах).
    """
    img = Image.open(src_path).convert("P")
    palette = _get_palette_rgb(img)
    indexed, orig_to_pos, pos_to_orig = _build_sorted_tables(palette)
    w, h = img.size
    pixels = img.load()

    # сформировать последовательность бит
    bits: List[int] = []
    if use_header_len:
        total_bits = len(bitstream)
        header = total_bits.to_bytes(4, "big")
        for byte in header:
            for i in range(8)[::-1]:
                bits.append((byte >> i) & 1)
    for b in bitstream:
        for i in range(8)[::-1]:
            bits.append((b >> i) & 1)

    capacity = w * h
    if len(bits) > capacity:
        raise ValueError(f"Недостаточная емкость: нужно {len(bits)} пикс., есть {capacity}")

    n = len(indexed)  # обычно 256
    k = 0
    for y in range(h):
        for x in range(w):
            if k >= len(bits):
                break
            orig_idx = pixels[x, y]
            pos = orig_to_pos[orig_idx]
            target_bit = bits[k]
            new_pos = _nearest_pos_with_lsb(target_bit, pos, n)
            new_orig = pos_to_orig[new_pos]
            pixels[x, y] = new_orig
            k += 1
        if k >= len(bits):
            break

    img.save(dst_path)

def extract_palette_lsb(
    stego_path: str,
    max_bits: int | None = None,
    use_header_len: bool = True
) -> bytes:
    img = Image.open(stego_path).convert("P")
    palette = _get_palette_rgb(img)
    _, orig_to_pos, _ = _build_sorted_tables(palette)
    w, h = img.size
    pixels = img.load()

    bits: List[int] = []
    for y in range(h):
        for x in range(w):
            pos = orig_to_pos[pixels[x, y]]
            bits.append(pos & 1)
            if max_bits is not None and len(bits) >= max_bits:
                break
        if max_bits is not None and len(bits) >= max_bits:
            break

    # если есть заголовок длины
    if use_header_len:
        if len(bits) < 32:
            raise ValueError("Недостаточно битов для заголовка длины")
        hdr_bits = bits[:32]
        length_bits = 0
        for b in hdr_bits:
            length_bits = (length_bits << 1) | b
        payload_bits = bits[32:32+length_bits]
    else:
        payload_bits = bits if max_bits is None else bits[:max_bits]

    # собрать байты
    out = bytearray()
    for i in range(0, len(payload_bits), 8):
        chunk = payload_bits[i:i+8]
        if len(chunk) < 8:
            break
        v = 0
        for b in chunk:
            v = (v << 1) | b
        out.append(v)
    return bytes(out)

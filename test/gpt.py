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

def _rgb_dist2(a, b):
    dr = a[0]-b[0]; dg = a[1]-b[1]; db = a[2]-b[2]
    return dr*dr + dg*dg + db*db

def _nearest_index_with_lsb_by_color(target_bit: int, orig_idx: int, palette: List[Tuple[int,int,int]], T_max: int = 40, k_max: int = 16):
    """
    Возвращает индекс палитры, наиболее близкий по цвету к orig_idx,
    среди тех, у кого (idx & 1) == target_bit. Ограничивает поиск k_max лучшими.
    T_max — максимум допустимой квадратной ошибки; если лучший хуже — вернёт None.
    """
    base = palette[orig_idx]
    best_idx = None
    best_d2 = 10**9
    # Быстрый двухпроходный поиск с отсечкой:
    # 1) Пробуем ближайшие индексы по локальному диапазону вокруг orig_idx (±8) — часто достаточно.
    for radius in (1, 2, 4, 8):
        for sign in (-1, +1):
            j = orig_idx + sign*radius
            if 0 <= j < len(palette) and (j & 1) == target_bit:
                d2 = _rgb_dist2(base, palette[j])
                if d2 < best_d2:
                    best_d2 = d2
                    best_idx = j
        if best_d2 <= T_max:
            return best_idx
    # 2) Глобальный редуцированный поиск: просматриваем палитру с шагом, чтобы найти до k_max кандидатов.
    # Это дешево при 256 цветах.
    candidates = []
    for j in range(len(palette)):
        if (j & 1) != target_bit:
            continue
        d2 = _rgb_dist2(base, palette[j])
        candidates.append((d2, j))
    candidates.sort(key=lambda x: x[0])
    if not candidates:
        return None
    # выбираем лучший в пределах порога; иначе возьмем лучший, если он не хуже T_max
    best_d2, best_idx = candidates[0]
    if best_d2 <= T_max:
        return best_idx
    # Если лучший хуже порога — считаем, что менять нельзя
    return None

def embed_palette_lsb_nohdr(src_path: str, dst_path: str, payload: bytes):
    img = Image.open(src_path).convert("P")
    palette = _get_palette_rgb(img)
    _, orig_to_pos, pos_to_orig = _build_sorted_tables(palette)

    w, h = img.size
    pixels = img.load()

    bits: List[int] = []
    for b in payload:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)

    capacity = w * h
    # Теоретическая емкость сохраняется, но из-за порога часть пикселей может быть пропущена.
    if len(bits) > capacity:
        raise ValueError(f"Недостаточная емкость: нужно {len(bits)} бит, есть {capacity}")

    n = 256
    k = 0
    # Порог и параметры поиска — подберите под свой набор изображений
    T_max = 40   # ~ среднее отклонение ≈ sqrt(40) ≈ 6.3 уровней по каналу
    for y in range(h):
        for x in range(w):
            if k >= len(bits):
                break
            orig_idx = pixels[x, y]
            # предпочтительно вообще не менять, если уже совпадает
            pos = orig_to_pos[orig_idx]
            target = bits[k]
            if (pos & 1) == target:
                k += 1
                continue
            # Подбор ближайшего по цвету индекса с нужным LSB
            new_idx = _nearest_index_with_lsb_by_color(target, orig_idx, palette, T_max=T_max)
            if new_idx is None:
                # Слишком большое искажение — не меняем этот пиксель, переносим бит дальше
                continue
            pixels[x, y] = new_idx
            k += 1
        if k >= len(bits):
            break

    if k < len(bits):
        raise ValueError(f"Не удалось вместить все биты без заметных искажений: записано {k} из {len(bits)}. "
                         f"Понизьте T_max или нагрузку.")

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
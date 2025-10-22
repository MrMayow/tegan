from PIL import Image

def display_palette(palette, save_path):
    result_palette = []
    for x in palette:
        result_palette.extend([x[1], x[2], x[3]])
    # Размеры: ширина 256 (индексы), высота 20 (прямоугольник)
    width, height = 256, 20
    palette_img = Image.new('P', (width, height))

    # Заполнение: каждый пиксель по x = индекс, одинаково по всем y
    pixels = []
    for y in range(height):
        row = list(range(width))  # [0,1,2,...,255] слева направо
        pixels.extend(row)

    palette_img.putdata(pixels)
    palette_img.putpalette(result_palette, rawmode='RGB')
    palette_img.save(save_path)  # Или 'palette.bmp' для BMP-формата

def _get_palette_rgb(img: Image.Image):
    assert img.mode == "P", "Нужно палитровое изображение 8 bpp"
    pal = img.getpalette()  # flat list [R0,G0,B0, R1,G1,B1, ...]
    # ограничим 256*3 элементов
    pal = pal[:256*3]
    return [(pal[i], pal[i+1], pal[i+2]) for i in range(0, len(pal), 3)]

def _weight(rgb) -> int:
    r,g,b = rgb
    return (r<<16) + (g<<8) + b  # W = 65536*R + 256*G + B

def _build_sorted_tables(palette):
    # Tsort: список кортежей (orig_index, rgb) отсортированный по W
    indexed = list(enumerate(palette))
    indexed.sort(key=lambda x: _weight(x[1]))
    # отображения
    orig_to_pos = {orig:i for i,(orig,_) in enumerate(indexed)}
    pos_to_orig = {i:orig for i,(orig,_) in enumerate(indexed)}
    return indexed, orig_to_pos, pos_to_orig   

def _nearest_pos_with_lsb(target_bit, pos_to_orig, pos, n):
    orig = pos_to_orig[pos]
    if (orig & 1) == target_bit:
        return orig
    r = 1
    while True:
        dn = pos - r
        up = pos + r
        orig_dn = pos_to_orig[dn]
        orig_up = pos_to_orig[up]
        cand = []
        if orig_dn >= 0 and ((orig_dn & 1) == target_bit):
            cand.append(orig_dn)
        if orig_up < n and ((orig_up & 1) == target_bit):
            cand.append(orig_up)
        if cand:
            return min(cand, key=lambda c: abs(c - pos))
        if orig_dn < 0 and orig_up >= n:
            return orig
        r += 1
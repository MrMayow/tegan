from PIL import Image

def sort_palette_by_index(colors, index):
    """
    Сортирует палитру по красному каналу (элемент с индексом 1)
    Сохраняет исходный индекс (элемент с индексом 0)
    
    Args:
        colors: список кортежей (index, R, G, B)
        
    Returns:
        list: отсортированный список цветов
    """
    # Сортируем по элементу [1] - это красный канал (R)
    return sorted(colors, key=lambda x: x[index])

def save_with_new_table(path : str, new_path : str, new_palette : list):
        

    # Загрузка изображения (должно быть 8-битным, режим 'P')
    im = Image.open(path)
    if im.mode != 'P':
        im = im.convert('P')  # Конвертация в палитровый режим, если нужно

    # Пример: создание инвертированной палитры (оригинал -> 255 - значение)
    original_palette = list(im.getpalette())  # Получить текущую палитру (768 значений)
    inverted_palette = [(255 - val) % 256 for val in original_palette]  # Инверсия

    # Прикрепление палитры
    result_palette = []
    for x in new_palette:
        result_palette.extend([x[1], x[2], x[3]])
    
    print(result_palette)
    im.putpalette(result_palette, rawmode='RGB')

    # Сохранение в BMP (палитра сохранится в заголовке)
    im.save(new_path, format='BMP')

    print(f"Палитра записана в {new_path}")

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


    

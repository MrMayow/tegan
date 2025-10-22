from PIL import Image

def extract_bmp_palette_grok(image_path):
    """
    Извлекает таблицу цветов (палитру) из BMP-файла с индексами.
    
    Args:
        image_path (str): Путь к BMP-файлу.
    
    Returns:
        list: Список кортежей (index, R, G, B) для цветов палитры.
    """
    try:
        with Image.open(image_path) as img:
            if img.mode != 'P':
                print("Изображение не палитровое (режим: {}), палитры нет.".format(img.mode))
                return []
            
            # Получаем палитру как байты (каждый цвет: B, G, R, [A=0])
            palette_bytes = img.getpalette()
            
            # Преобразуем в список (index, RGB)-кортежей
            palette = []
            for i in range(0, len(palette_bytes), 3):
                if i + 2 < len(palette_bytes):
                    r = palette_bytes[i + 2]  # R в конце
                    g = palette_bytes[i + 1]  # G
                    b = palette_bytes[i]      # B в начале
                    index = len(palette)      # Индекс от 0
                    palette.append((index, r, g, b))
            
            return palette
    except Exception as e:
        print("Ошибка при чтении файла: {}".format(e))
        return []


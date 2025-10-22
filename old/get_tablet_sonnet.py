from PIL import Image
import struct

def extract_bmp_palette_sonnet(bmp_path):
    """
    Извлекает таблицу цветов (палитру) из BMP изображения через PIL
    
    Args:
        bmp_path: путь к BMP файлу
        
    Returns:
        list: список кортежей (index, R, G, B)
    """
    img = Image.open(bmp_path)
    
    if img.mode != 'P':
        print(f"Изображение не использует палитру. Режим: {img.mode}")
        return None
    
    palette = img.getpalette()
    
    if palette is None:
        print("Палитра не найдена")
        return None
    
    # Добавляем индекс к каждому цвету
    colors = []
    for i in range(0, len(palette), 3):
        index = i // 3
        r = palette[i]
        g = palette[i + 1]
        b = palette[i + 2]
        colors.append((index, r, g, b))
    
    return colors


def extract_bmp_palette_manual(bmp_path):
    """
    Извлекает таблицу цветов напрямую из файла BMP
    
    Args:
        bmp_path: путь к BMP файлу
        
    Returns:
        list: список кортежей (index, R, G, B)
    """
    with open(bmp_path, 'rb') as f:
        bmp_header = f.read(14)
        if bmp_header[:2] != b'BM':
            print("Это не BMP файл")
            return None
        
        dib_header_size = struct.unpack('<I', f.read(4))[0]
        f.seek(14)
        dib_header = f.read(dib_header_size)
        bits_per_pixel = struct.unpack('<H', dib_header[14:16])[0]
        
        if bits_per_pixel <= 8:
            if dib_header_size >= 36:
                num_colors = struct.unpack('<I', dib_header[32:36])[0]
                if num_colors == 0:
                    num_colors = 2 ** bits_per_pixel
            else:
                num_colors = 2 ** bits_per_pixel
        else:
            print(f"BMP не использует палитру (bpp={bits_per_pixel})")
            return None
        
        f.seek(14 + dib_header_size)
        
        colors = []
        for index in range(num_colors):
            color_data = f.read(4)
            b, g, r, reserved = struct.unpack('BBBB', color_data)
            colors.append((index, r, g, b))
        
        return colors





def print_palette(colors, show_hex=True):
    """
    Выводит палитру в читаемом формате
    
    Args:
        colors: список кортежей (index, R, G, B)
        show_hex: показывать ли HEX представление
    """
    print(f"Всего цветов в палитре: {len(colors)}\n")
    if show_hex:
        print(f"{'Индекс':<8} {'RGB':<20} {'HEX':<10}")
        print("-" * 38)
    else:
        print(f"{'Индекс':<8} {'RGB':<20}")
        print("-" * 28)
    
    for index, r, g, b in colors:
        rgb_str = f"({r:3d}, {g:3d}, {b:3d})"
        if show_hex:
            hex_str = f"#{r:02X}{g:02X}{b:02X}"
            print(f"{index:<8} {rgb_str:<20} {hex_str:<10}")
        else:
            print(f"{index:<8} {rgb_str:<20}")


from PIL import Image


def convert_to_8bit_bmp(input_path, output_path):
    # Открываем изображение
    image = Image.open(input_path)
    
    # Конвертируем в режим 'P' (8-бит палитровый)
    # Квантизация для ограничения до 256 цветов
    quantized_image = image.quantize(colors=256, method=2)  # method=2 для медианной квантизации
    
    # Сохраняем как BMP (автоматически с палитрой)
    quantized_image.save(output_path, format='BMP')
    
    print(f"Преобразовано: {input_path} -> {output_path}")
    return quantized_image

convert_to_8bit_bmp("OIP.jpg", "OIPBPM.bmp")
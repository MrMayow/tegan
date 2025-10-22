from ast import List
from PIL import Image
from utils import display_palette, _get_palette_rgb, _build_sorted_tables, _weight, _nearest_pos_with_lsb

stringa = "На краю дороги стоял дуб. Вероятно, в десять раз старше берез, составлявших лес, он был в десять раз толще, и в два раза выше каждой березы. Это был огромный, в два обхвата дуб, с обломанными, давно, видно, суками и с обломанной корой, заросшей старыми болячками. С огромными своими неуклюже, несимметрично растопыренными корявыми руками и пальцами, он старым, сердитым и презрительным уродом стоял между улыбающимися березами. Только он один не хотел подчиняться обаянию весны и не хотел видеть ни весны, ни солнца. Князь Андрей несколько раз оглянулся на этот дуб, проезжая по лесу, как будто он чего-то ждал от него. Цветы и трава были и под дубом, но он все так же, хмурясь, неподвижно, уродливо и упорно, стоял посреди их. «Да, он прав, тысячу раз прав этот дуб, — думал князь Андрей, — пускай другие, молодые, вновь поддаются на этот обман, а мы знаем жизнь, — наша жизнь кончена!» Целый новый ряд мыслей безнадежных, но грустно-приятных в связи с этим дубом возник в душе князя Андрея. Во время этого путешествия он как будто вновь обдумал всю свою жизнь и пришел к тому же прежнему, успокоительному и безнадежному, заключению, что ему начинать ничего было не надо, что он должен доживать свою жизнь, не делая зла, не тревожась и ничего не желая."

def str_to_bit_array(s, encoding='utf-8'):
    bytes_data = s.encode(encoding)
    bit_array = []
    for byte in bytes_data:
        binary = bin(byte)[2:].zfill(8)
        bit_array.extend([int(bit) for bit in binary])
    return bit_array

def embed_palette(source_path, dst_path, bits):
    source_image_path = source_path
    dst_path = dst_path
    image = Image.open(source_image_path).convert("P")
    palette = _get_palette_rgb(image)
    sorted_palette, orig_to_pos, pos_to_orig = _build_sorted_tables(palette)
    pixels = image.load()
    bits = str_to_bit_array(stringa)
    print(len(bits))
    w, h = image.size
    pixels = image.load()

    n = 256
    k = 0
    for x in range(w):
        for y in range(h):
            if k >= len(bits): break
            orig_idx = pixels[x, y]
            pos = orig_to_pos[orig_idx]
            target = bits[k]
            new_pos = _nearest_pos_with_lsb(target, pos_to_orig ,pos, n)
            pixels[x, y] = new_pos
            k += 1
            
        if k >= len(bits): break
        
    
    image.save(dst_path)

def extract_palette(img_path, bit_len):
    image = Image.open(img_path).convert("P")
    palette = _get_palette_rgb(image)
    w, h = image.size
    pixels = image.load()
    bits: List[int] = []
    need = bit_len
    for x in range(w):
        for y in range(h):
            if len(bits) >= need: break
            pixel_pos = pixels[x, y]
            bits.append(pixel_pos & 1)
        if len(bits) >= need: break
    return bits

embed_palette("cat.bmp", "result.bmp", "A")
result_b = extract_palette("result.bmp", 18024)
print(result_b)





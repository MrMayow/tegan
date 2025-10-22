from get_tablet_grok import extract_bmp_palette_grok
from get_tablet_sonnet import extract_bmp_palette_sonnet
from utils import display_palette, sort_palette_by_index
from to_bmp import convert_to_8bit_bmp  
from utils import save_with_new_table



orig_path = "orig.jpg"
bmp_path = "cat.bmp"  # Замените на путь к вашему файлу
new_bmp_path = "cat_modified.bmp"
convert_to_8bit_bmp(orig_path, bmp_path)

# tablet = extract_bmp_palette_grok(bmp_path)
# print("Палитра из get_tablet_grok:", tablet)

tablet = extract_bmp_palette_sonnet(bmp_path)
print("Палитра из get_tablet_sonnet:", tablet)
display_palette(tablet, "default tablet.bmp")
sorted_tablet = sort_palette_by_index(tablet, 1)
display_palette(sorted_tablet, "sorted tablet.bmp")
#save_with_new_table(bmp_path, new_bmp_path, tablet)
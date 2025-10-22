from utils import *

secret = b"Hello my fdfksdfjsdlkfsdjfslk;dfjslkddfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjfdfjslkdfjlksdjffjlksdjf;lksdjfklsjdflksjdflksjdfjsdkjgj5rtjgohdfogdfjgodfigj"
embed_palette_lsb_nohdr("cat.bmp", "stego.bmp", secret)
restored = extract_palette_lsb_nohdr("stego.bmp", len(secret)*8)
print(restored, restored == secret)


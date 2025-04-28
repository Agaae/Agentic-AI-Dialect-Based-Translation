import pytesseract
from PIL import Image
import arabic_reshaper
from bidi.algorithm import get_display
# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\ahmed\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"




def extract_text_from_image(image_path):
    # Load image
    image = Image.open(image_path)

    # Extract Arabic + English text
    raw_text = pytesseract.image_to_string(image, lang='ara')

    # Reshape Arabic text
    reshaped_text = arabic_reshaper.reshape(raw_text)

    # Fix right-to-left display (for visual display)
    bidi_text = get_display(raw_text)

    return bidi_text  # This is the reshaped and properly displayed text



def extract_text_from_image_eng(image_path):
    # Load image
    image = Image.open(image_path)

    # Extract Arabic + English text
    raw_text = pytesseract.image_to_string(image, lang='eng')

    # Reshape Arabic text
    reshaped_text = arabic_reshaper.reshape(raw_text)

    # Fix right-to-left display (for visual display)
    bidi_text = get_display(raw_text)

    return bidi_text  # This is the reshaped and properly displayed text



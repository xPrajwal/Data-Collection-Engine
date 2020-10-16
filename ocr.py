from PIL import Image
import pytesseract

def recognise(image_path):
	imageFile = Image.open(image_path)
	text = pytesseract.image_to_string(imageFile, lang = 'eng')
	print(text)
	return text

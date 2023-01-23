import pytesseract


def image_to_text(img):
    return pytesseract.image_to_data(img, lang="ita+en",output_type=pytesseract.Output.DICT, config='--psm 3')



def extract_text(img, left,top,width,height, conf):
  # Cropping the text block for giving input to OCR
  cropped = img[top:top + height, left:left + width]
  config = ('-l ita+en  --psm '+str(conf))
  text = pytesseract.image_to_string(cropped, config=config)
 
  return text

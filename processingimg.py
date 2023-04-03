import math

import cv2
import numpy as np
from PIL import Image

# import pytesseract
# from pytesseract import Output
from ocr import image_to_text, extract_text


def array_to_img(matrix):
    return Image.fromarray(matrix)


def remove_img_on_pdf(idoc):
    for i in range(len(idoc)):
        img_list = idoc.get_page_images(i)
        con_list = idoc[i].get_contents()

        for j in con_list:
            c = idoc.xref_stream(j)  # read the stream source
            # print(c)
            if c is not None:
                for v in img_list:
                    arr = bytes(v[7], 'utf-8')
                    r = c.find(arr)  # try find the image display command
                    if r != -1:
                        cnew = c.replace(arr, b"")
                        idoc.update_stream(j, cnew)
                        c = idoc.xref_stream(j)
    return idoc


def pix_to_image(pix):
    bytes = np.frombuffer(pix.samples, dtype=np.uint8)
    img = bytes.reshape(pix.height, pix.width, pix.n)
    return img


def preprocessing(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # gray=cv2.threshold(img,127,255,cv2.THRESH_BINARY)

    # img_threshold=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
    img_threshold = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 3, 1)
    return img_threshold


def draw_blocks(img, blocks, zoom1, zoom2):
    for i in range(len(blocks)):
        print()
        (left_i, top_i, width_i, height_i) = (
            blocks[i]['x'] * zoom1, blocks[i]['y'] * zoom2, blocks[i]['width'] * zoom1, blocks[i]['height'] * zoom2)
        left_i = math.ceil(left_i)
        top_i = math.ceil(top_i)
        width_i = round(width_i)
        height_i = round(height_i)
        cv2.rectangle(img, (left_i, top_i), (left_i + width_i, top_i + height_i), (0, 255, 0), 2)


def search_words(img):
    text = image_to_text(img)

    n_boxes = len(text['level'])
    words = []

    # cicla su tutti i blocchi di testo present
    for i in range(n_boxes):

        if text['level'][i] == 5:
            (left_i, top_i, width_i, height_i) = \
                (text['left'][i] - 3, text['top'][i] - 3, text['width'][i] + 6, text['height'][i] + 6)

            # controllo (non posso fa di più se no si prende i caratteri tipo :) --> si può anche cancellare a sto punto
            if height_i <= 6:
                continue
            if height_i >= 30 and width_i <= 8:
                continue
            if height_i >= 60 and width_i >= 100:
                continue
            if height_i >= 80 or width_i >= 450:
                continue

            # dovresti provare a leggere già dal pdf
            text_block = extract_text(img, left_i, top_i, width_i, height_i, 7)
            text_block2 = text_block.replace(" ", "")
            if len(text_block2) > 0:
                if width_i >= 100 and len(text_block2) <= 4:
                    continue

                # rimuovere blocchi molto lunghi o molto larghi o che sono quadrati grandi rimuovere caratteri
                # speciali e vedere se la stringa è vuota rimuovere blocchi grandi di una certa dimensione e che
                # togliendo i caratteri speciali contengono poco testo

                word = {}
                for key in text.keys():
                    if key == "left" or key == "top" or key == "height" or key == "width":
                        word[key] = text[key][i]
                    if key == "text":
                        word[key] = text[key][i]

                words.append(word)

    return words

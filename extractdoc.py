from processingblocks import search_blocks_miner, search_blocks_ocr, clean_remove_blocks, remove_empty_blocks, union_blocks, text_from_blocks, order_top_left
from processingimg import pix_to_image, draw_blocks, preprocessing, search_words
from processingpdf import extract_words_rects, remove_img_in_pdf, save_cv
from utilities import create_idfolder, clean_dir
import pytesseract

import fitz, json, pdfquery


def extract_pdf (file):

    id_folder = create_idfolder()
    file_path = save_cv (file, id_folder)


    (words,rects)= extract_words_rects(file_path)
    
    doc = fitz.open(file_path)
    zoom = 2    # zoom factor
    mat = fitz.Matrix(zoom, zoom)
    numpages = len(words)
    numblocks=0

    for page_i in range(numpages):
    
        numblocks+=len(words[page_i])
    
    if (numblocks!=0):
        
        blocks = use_pdfminer(doc, words, rects, mat)

    else:

        blocks = use_ocr(file_path, doc, mat)


    #ordina i blocchi per top e left

    order_top_left (blocks)

    # convert into json
    #blocks = json.dumps(blocks, ensure_ascii=False) 

    doc.close()
        
    clean_dir()

    return blocks




def use_pdfminer(doc,words,rects,mat):

    imgs = []
    blocks_text = []
    j=0

    for page in doc:

        pix = page.get_pixmap(matrix = mat)
        img = pix_to_image(pix)
        zoom1=img.shape[1]/page.mediabox[2]
        zoom2=img.shape[0]/page.mediabox[3]
        img = img.copy() #img precedente non modificabile (per risolvere alternativa downgrade versione numpy)
        blocks = search_blocks_miner(words[j],rects[j])
        blocks = clean_remove_blocks(blocks) #rimuovi simboli in blocchi o blocchi inutili 
        draw_blocks(img,blocks,zoom1,zoom2)
        imgs.append(img)
        blocks_text.append(blocks)
        j+=1

    
    return blocks_text


def use_ocr(file, doc, mat):
    pdfq = pdfquery.PDFQuery(file)
    rdoc = remove_img_in_pdf(doc)
    imgs = []
    blocks_text = []
    j=0
    for page in rdoc:
        height_image = page.mediabox[3]
        pdfq.load(j)
        pix = page.get_pixmap(matrix = mat)
        img = pix_to_image(pix)
        img = img.copy() #img precedente non modificabile (per risolvere alternativa downgrade versione numpy)
        img_prepro = preprocessing(img)

        #decommenta e modifica il path se necessario
        pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

        words = search_words(img_prepro)
        words = remove_empty_blocks(words,height_image,pdfq)
        blocks = search_blocks_ocr(words)
        blocks = union_blocks(blocks)

        #estrai testo da pdf.. se non c'è testo salta
        blocks = text_from_blocks(blocks,height_image,pdfq)

        blocks = clean_remove_blocks(blocks) #rimuovi simboli in blocchi o blocchi inutili

        zoom1=img.shape[1]/page.mediabox[2]
        zoom2=img.shape[0]/page.mediabox[3]    
        draw_blocks(img,blocks,zoom1,zoom2)
        blocks_text.append(blocks)
        imgs.append(img)
        j+=1       
    
    pdfq.file.close()

    return blocks_text
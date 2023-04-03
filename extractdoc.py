import fitz
import pdfquery
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO


from processingblocks import search_blocks_miner, search_blocks_ocr, clean_remove_blocks, remove_empty_blocks, \
    union_blocks, text_from_blocks, order_top_left, convert_to_blocks
from processingimg import pix_to_image, draw_blocks, preprocessing, search_words
from processingpdf import extract_words_rects, remove_img_in_pdf, save_cv
from utilities import create_idfolder, clean_dir


def test(file):
    text = []
    pages = convert_from_bytes(file)
    i = 0
    for page in pages:
        buffer = BytesIO()
        page.save(buffer, 'PNG')
        img_buffer = buffer.getvalue()

        # utilizza pytesseract per estrarre il testo dall'immagine
        text[i] = pytesseract.image_to_string(img_buffer)
        i += 1
    return text


def extract_pdf(file):
    blocks = []
    id_folder = create_idfolder()
    file_path = save_cv(file, id_folder)

    (words, rects) = extract_words_rects(file_path)

    document = fitz.open(file_path)
    # set resolution image
    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    num_pages = len(words)
    num_blocks = 0

    for index_page in range(num_pages):
        num_blocks += len(words[index_page])

    if num_blocks != 0:
        blocks = use_pdfminer(document, words, rects, mat)

    else:

        blocks = use_ocr(file_path, document, mat)

    # ordina i blocchi per top e left

    if len(blocks) != 0:
        order_top_left(blocks)

    # convert into json
    # blocks = json.dumps(blocks, ensure_ascii=False)

    document.close()

    clean_dir()

    return blocks


def use_pdfminer(doc, words, rects, mat):
    imgs = []
    blocks_text = []
    j = 0

    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        img = pix_to_image(pix)
        zoom1 = img.shape[1] / page.mediabox[2]
        zoom2 = img.shape[0] / page.mediabox[3]
        img = img.copy()  # img precedente non modificabile (per risolvere alternativa downgrade versione numpy)
        blocks = search_blocks_miner(words[j], rects[j])
        blocks = clean_remove_blocks(blocks)  # rimuovi simboli in blocchi o blocchi inutili
        draw_blocks(img, blocks, zoom1, zoom2)
        imgs.append(img)
        blocks_text.append(blocks)
        j += 1

    return blocks_text


def use_ocr(file_path, document, mat):
    rects = []
    pdf = pdfquery.PDFQuery(file_path)
    rdoc = remove_img_in_pdf(document)
    imgs = []
    blocks_text = []
    j = 0
    for page in rdoc:
        height_image = page.mediabox[3]
        pdf.load(j)
        pix = page.get_pixmap(matrix=mat)
        img = pix_to_image(pix)
        img = img.copy()  # img precedente non modificabile (per risolvere alternativa downgrade versione numpy)
        img_prepro = preprocessing(img)

        # decommenta e modifica il path se necessario
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

        words = search_words(img_prepro)
        # words = remove_empty_blocks(words, height_image, pdf)
        # words = remove_text_empty(words)
        blocks = convert_to_blocks(words)
        # blocks = search_blocks_ocr(words)
        # blocks = union_blocks(blocks)

        blocks = search_blocks_miner(blocks, rects)

        # estrai testo da pdf.. se non c'è testo salta
        # blocks = text_from_blocks(blocks, height_image, pdf)

        # rimuovi simboli in blocchi o blocchi inutili
        # blocks = clean_remove_blocks(blocks)

        # zoom1 = img.shape[1] / page.mediabox[2]
        # zoom2 = img.shape[0] / page.mediabox[3]
        # draw_blocks(img, blocks, zoom1, zoom2)
        blocks_text.append(blocks)
        # imgs.append(img)
        j += 1

    pdf.file.close()

    return blocks_text

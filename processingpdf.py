from pdfminer.layout import LAParams, LTText, LTChar, LTAnno, LTTextLineHorizontal, LTRect
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.converter import PDFPageAggregator

import math

import os
from docx2pdf import convert

import win32com.client
import pythoncom
import re
from werkzeug.utils import secure_filename


def extract_words_rects(file):
    cv_words=[] #lista di parole
    cv_rects = [] #lista di oggetti rects
    fp = open(file, 'rb')
    manager = PDFResourceManager()
    laparams = LAParams()
    dev = PDFPageAggregator(manager, laparams=laparams)
    interpreter = PDFPageInterpreter(manager, dev)
    pages = PDFPage.get_pages(fp)
    for page in pages:
        width_page=page.mediabox[2]
        height_page=page.mediabox[3]
        rects=[]
        blocks=[]
        interpreter.process_page(page)
        layout = dev.get_result()
        x, y, text = -1, -1, ''
        for textbox in layout:
            if isinstance(textbox, LTRect):
                rect={}
                rect['x']=textbox.x0
                rect['y']=height_page-textbox.y1
                rect['width']=textbox.width
                rect['height']=textbox.height
                rects.append(rect)
                continue

            if isinstance(textbox, LTText):

              for line in textbox:
                if isinstance(line, LTTextLineHorizontal):

                  for char in line:
                      # If the char is a line-break or an empty space, the word is complete
                    if isinstance(char, LTAnno) or char.get_text() == ' ':
                      if x != -1:
                          if (text.strip()==""):
                            continue

                          #print('%r : %s' % ((x, y), text))
                          block={}
                          block['x']=x
                          block['y']=y
                          block['width']=width
                          block['height']=height
                          block['text']=text
                          blocks.append(block)
                      x, y, text = -1, -1, ''
                    elif isinstance(char, LTChar):
                      text += char.get_text()
                      if x == -1: #primo carattere parola
                        x, y, width, height = char.x0, height_page-char.y1,char.width, char.height
                      else: #parola che contiene già caratteri
                        y=min(y,height_page-char.y1)
                        width=width+char.width #width_word+width_newchar
                        height=max(height,char.height)

          # If the last symbol in the PDF was neither an empty space nor a LTAnno, print the word here
        if x != -1:
          if (text.strip()==""):
            continue

          #print('At %r : %s' % ((x, y), text))
          block={}
          block['x']=x
          block['y']=y
          block['width']=width
          block['height']=height
          block['text']=text
          blocks.append(block)
        cv_words.append(blocks)
        cv_rects.append(rects)

    fp.close()
      
    return (cv_words,cv_rects)


def remove_img_in_pdf(idoc):

  for i in range(len(idoc)):
    img_list = idoc.get_page_images(i)
    con_list = idoc[i].get_contents()

    for j in con_list:
        c = idoc.xref_stream(j) # read the stream source
        #print(c)
        if c != None:
            for v in img_list: 
                arr = bytes(v[7], 'utf-8')
                r = c.find(arr) # try find the image display command
                if r != -1:
                    cnew = c.replace(arr, b"")
                    idoc.update_stream(j, cnew)
                    c = idoc.xref_stream(j)
  return idoc


def extract_text_pdfquery(x,y,width,height,height_image,pdf):
  x = math.ceil(x/2)
  y = math.ceil(y/2)
  width = round(width/2)
  height = round(height/2)
  #ho bisogno di ridurre un po' altezza e profondità perchè può capitare che mi legge più testo
  width_reduced = math.ceil(width*0.9)
  y0 = height_image - y - round(height*0.1)
  y1 = y0-math.ceil(height*0.9)
  text = pdf.pq('LTTextLineHorizontal:overlaps_bbox("'+str(x)+','+str(y1)+','+str(x+width_reduced)+','+str(y0)+'")').text()


  return (x,y,height,width,text)


def save_cv (f, id_folder):

  file_name = secure_filename(f.filename)

  folder = os.path.join("static",id_folder)
   
  os.mkdir(folder)

  path_cv = os.path.join(folder, file_name)
      
  split_tup = os.path.splitext(file_name)

  f.save(path_cv) #è la stessa cosa che faccio sopra.. mette i / in automatico
      
      #crea una com
  win32com.client.Dispatch("Word.Application", pythoncom.CoInitialize())

  if split_tup[1]=='.doc':

    path_docx = save_as_docx(path_cv)
    return save_as_pdf(path_docx)


  if split_tup[1]=='.docx':
    return save_as_pdf(path_cv)
  

  return path_cv
  


def save_as_docx(path_cv):
    # Opening MS Word
    
    path_cv_abs=os.path.abspath(path_cv)
    word = win32com.client.gencache.EnsureDispatch('Word.Application')
    doc = word.Documents.Open(path_cv_abs)
    doc.Activate ()

    # Rename path with .docx
    #new_file_abs = os.path.abspath(path)
    new_path_cv_abs = re.sub(r'\.\w+$', '.docx', path_cv_abs)
    new_path_cv = re.sub(r'\.\w+$', '.docx', path_cv)


    # Save and Close
    word.ActiveDocument.SaveAs(
        new_path_cv_abs, FileFormat=win32com.client.constants.wdFormatXMLDocument
    )
    doc.Close(False)

    return new_path_cv


def save_as_pdf(path):
      #crea una com
  win32com.client.gencache.EnsureDispatch('Word.Application')
  outputFile = re.sub(r'\.\w+$', '.pdf', path)
  file = open(outputFile, "w")
  file.close()
  convert(path, outputFile)
  return outputFile
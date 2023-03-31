import re

from processingpdf import extract_text_pdfquery


def search_blocks_miner(words, rects):
    blocks = []
    finish = 1
    while finish == 1:
        finish = 0
        n_words = len(words)

        for i in range(n_words):
            (left_i, top_i, width_i, height_i) = (words[i]['x'], words[i]['y'], words[i]['width'], words[i]['height'])
            for j in range(n_words):
                (left_j, top_j, width_j, height_j) = (
                    words[j]['x'], words[j]['y'], words[j]['width'], words[j]['height'])

                if (i != j):
                    # meglio il min perchè se sono stessa riga di testo molto probabilmente hanno anche una simile
                    # altezzza --> sfavorisce blocchi vicini con altezze abbastanza diverse
                    if (left_j + width_j >= left_i + width_i >= left_j - min(height_i,
                                                                             height_j) * 0.95 and top_j + height_j <= top_i + height_i + 6 and top_j >= top_i - 6):  # and left_iplus - height_i <=  left_i+width_i

                        separate = separate_rect(left_i, top_i, width_i, height_i, left_j, top_j, width_j, height_j,
                                                 rects, words[i]['text'], words[j]['text'])
                        if separate == True:
                            continue

                        words[i]['x'] = min(left_i, left_j)
                        words[i]['y'] = min(top_i, top_j)
                        words[i]['width'] = max(left_i + width_i, left_j + width_j) - words[i]['x']
                        words[i]['height'] = max(top_i + height_i, top_j + height_j) - words[i]['y']
                        words[i]['text'] = words[i]['text'] + ' ' + words[j]['text']
                        finish = 1
                        words.pop(j)
                        break
            if finish == 1:
                break

    for i in range(len(words)):

        block = {}
        for key in words[i].keys():
            block[key] = words[i][key]

        blocks.append(block)

    return blocks


def separate_rect(left_i, top_i, width_i, height_i, left_j, top_j, width_j, height_j, rects, text1, text2):
    for rect in rects:
        if (left_i + width_i <= rect['x'] and left_j + 3 >= rect['x'] + rect['width'] and ((min(top_i, top_j) < rect['y'] + rect['height'] < max(top_i + height_i,
                                                                                                      top_j + height_j)) or (rect['y'] >= min(top_i, top_j) and rect['y'] <= max(top_i + height_i, top_j + height_j)) or (rect['y'] <= min(top_i, top_j) and rect['y'] + rect['height'] >= max(top_i + height_i,
                                                                                       top_j + height_j)))):
            # basta che vedo se una lina separatrice inizia o temrina in mezzo o è intera

            return True


def clean_remove_blocks(blocks):
    index_to_delete = []
    for i in range(len(blocks)):
        text = blocks[i]['text']
        # or text_block=="o" or text_block=="▪" or text_block == "•" or text_block == "▫" ):
        text_modified = text.replace("o", "")
        text_modified = text_modified.replace("▪", "")
        text_modified = text_modified.replace("•", "")
        text_modified = text_modified.replace("▫", "")
        text_modified = text_modified.strip()

        if (len(text_modified) == 0):
            index_to_delete.append(i)
            continue

        text_block = re.sub('[^a-zA-Z0-9 \n\.]', '', text)
        text_block = text_block.strip()
        if (len(text_block) <= 1):  # cancella anche i simboli all'inizio della lista
            index_to_delete.append(i)
            continue
        text = text.replace("©", "").strip()
        allwords = text.split()
        if allwords[0] == '▫' or allwords[0] == 'o' or allwords[0] == "▪" or allwords[0] == "•":
            numwords = len(allwords)
            text = ""
            for j in range(1, numwords, 1):
                text = text + allwords[j]
                if (j != numwords):
                    text = text + " "

        # © togliere anche questo carattere

        blocks[i]['text'] = text.strip()

    num_blocks_delete = len(index_to_delete)
    if (num_blocks_delete > 0):
        for i in range(num_blocks_delete):
            blocks.pop(index_to_delete[i] - i)

    return blocks


def remove_empty_blocks(words, height_image, pdf):  # praticamente blocchi ocr non di testo che non sono stati filtrati
    index_to_delete = []
    for i in range(len(words)):
        (x, y, width, height) = (words[i]['left'], words[i]['top'], words[i]['width'], words[i]['height'])
        (x, y, width, height, text_block) = extract_text_pdfquery(x, y, width, height, height_image, pdf)
        text_block = text_block.replace(" ", "")

        if (len(text_block) <= 0):  # or text_block=="o" or text_block=="▪" or text_block == "•" or text_block == "▫" ):
            index_to_delete.append(i)

    num_blocks_delete = len(index_to_delete)
    if (num_blocks_delete > 0):
        for i in range(num_blocks_delete):
            words.pop(index_to_delete[i] - i)

    return words


def search_blocks_ocr(words):
    blocks = []
    finish = 1
    while finish == 1:
        finish = 0
        n_words = len(words)

        for i in range(n_words):
            (left_i, top_i, width_i, height_i) = (
                words[i]['left'], words[i]['top'], words[i]['width'], words[i]['height'])
            for j in range(n_words):
                (left_j, top_j, width_j, height_j) = (
                    words[j]['left'], words[j]['top'], words[j]['width'], words[j]['height'])

                if (i != j and left_j + width_j >= left_i + width_i and left_j - round(max(height_i, height_j) * 1.1,
                                                                                       0) <= left_i + width_i and top_j + height_j <= top_i + height_i + 6 and top_j >= top_i - 6):  # and left_iplus - height_i <=  left_i+width_i

                    words[i]['left'] = min(left_i, left_j)
                    words[i]['top'] = min(top_i, top_j)
                    words[i]['width'] = max(left_i + width_i, left_j + width_j) - words[i]['left']
                    words[i]['height'] = max(top_i + height_i, top_j + height_j) - words[i]['top']
                    finish = 1
                    words.pop(j)
                    break
            if finish == 1:
                break

    for i in range(len(words)):

        block = {}
        for key in words[i].keys():
            if key == 'top':
                block['y'] = words[i][key]
            if key == 'left':
                block['x'] = words[i][key]
            if key == 'width':
                block['width'] = words[i][key]
            if key == 'height':
                block['height'] = words[i][key]
            if key == 'text':
                block[key] = ''

        blocks.append(block)

    return blocks


def union_blocks(blocks):  # blocchi contenuti in altri blocchi

    finish = 1
    while finish == 1:
        finish = 0
        numblocks = len(blocks)
        # valuto se ci sono blocchi j contenuti in i
        # cicla su tutti i blocchi di testo presenti top_iplus >= top_i-6 ... top plus + height
        # plus  <= top + height +6
        for i in range(numblocks):
            (left_i, top_i, width_i, height_i) = (
                blocks[i]['x'], blocks[i]['y'], blocks[i]['width'], blocks[i]['height'])
            for j in range(numblocks):
                (left_j, top_j, width_j, height_j) = (
                    blocks[j]['x'], blocks[j]['y'], blocks[j]['width'], blocks[j]['height'])
                if i != j:
                    # Va a vedere tutti i casi di blocchi contenuti in altri (in tutte le posizioni possibili).
                    # Sicuramente c'è un modo per compattare le varie operazioni logiche CONTROLLARE
                    if ((
                            left_j + width_j <= left_i + width_i and left_j <= left_i and left_i <= left_j + width_j and top_j <= top_i and top_i <= top_j + height_j and top_j + height_j <= top_i + height_i) or \
                            (
                                    left_j + width_j >= left_i + width_i and left_j >= left_i and left_i + width_i >= left_j and top_j <= top_i and top_i <= top_j + height_j and top_j + height_j <= top_i + height_i) or \
                            (
                                    left_j + width_j <= left_i + width_i and left_j <= left_i and left_i <= left_j + width_j and top_j >= top_i and top_i + height_i >= top_j and top_j + height_j >= top_i + height_i) or \
                            (
                                    left_j + width_j >= left_i + width_i and left_j >= left_i and left_i + width_i >= left_j and top_j >= top_i and top_i + height_i >= top_j and top_j + height_j >= top_i + height_i) or \
                            (
                                    left_j + width_j <= left_i + width_i and left_j <= left_i and left_j + width_j >= left_i and top_j >= top_i and top_j + height_j <= top_i + height_i) or \
                            (
                                    left_j + width_j >= left_i + width_i and left_j >= left_i and left_i + width_i >= left_j and top_j >= top_i and top_j + height_j <= top_i + height_i) or \
                            (
                                    left_j + width_j <= left_i + width_i and left_j >= left_i and top_j <= top_i and top_i <= top_j + height_j and top_j + height_j <= top_i + height_i) or \
                            (
                                    left_j + width_j <= left_i + width_i and left_j >= left_i and top_j >= top_i and top_j <= top_i + height_i and top_j + height_j >= top_i + height_i) or \
                            (
                                    left_j + width_j >= left_i + width_i and left_j <= left_i and top_j <= top_i and top_i <= top_j + height_j and top_j + height_j <= top_i + height_i) or \
                            (
                                    left_j + width_j >= left_i + width_i and left_j <= left_i and top_j >= top_i and top_j + height_j <= top_i + height_i) or \
                            (
                                    left_j + width_j >= left_i + width_i and left_j <= left_i and top_j >= top_i and top_j <= top_i + height_i and top_j + height_j >= top_i + height_i) or \
                            (
                                    left_j + width_j >= left_i + width_i and left_j >= left_i and left_i + width_i >= left_j and top_j <= top_i + width_i and top_j <= top_i and top_j + height_j >= top_i + height_i) or \
                            (
                                    left_j + width_j <= left_i + width_i and left_j <= left_i and left_i <= left_j + width_j and top_j <= top_i and top_j + height_j >= top_i + height_i) or \
                            (
                                    left_j + width_j <= left_i + width_i and left_j >= left_i and top_j <= top_i and top_j + height_j >= top_i + height_i) or \
                            (
                                    left_j + width_j <= left_i + width_i and left_j >= left_i and top_j >= top_i and top_j + height_j <= top_i + height_i)):  # ultimo è blocco interamente contenuto

                        blocks[i]['x'] = min(left_i, left_j)
                        blocks[i]['y'] = min(top_i, top_j)
                        blocks[i]['width'] = max(left_i + width_i, left_j + width_j) - blocks[i]['x']
                        blocks[i]['height'] = max(top_i + height_i, top_j + height_j) - blocks[i]['y']
                        finish = 1
                        blocks.pop(j)
                        break
            if finish == 1:
                break

    return blocks


def text_from_blocks(blocks, height_image, pdf):
    text = []
    for i in range(len(blocks)):
        (x, y, width, height) = (blocks[i]['x'], blocks[i]['y'], blocks[i]['width'], blocks[i]['height'])

        x, y, height, width, text = extract_text_pdfquery(x, y, width, height, height_image, pdf)
        blocks[i]['x'] = x
        blocks[i]['y'] = y
        blocks[i]['height'] = height
        blocks[i]['width'] = width
        blocks[i]['text'] = text

    return blocks


def order_top_left(blocks):
    numpages = len(blocks)

    for i in range(numpages):
        blocks[i] = (sorted(blocks[i], key=lambda j: (int(j['y']), int(j['x']))))

    return

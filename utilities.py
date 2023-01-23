import shutil, os
from datetime import datetime
import random
import string


#questo file si chiamava save_results (nel caso dovessi poi prendere i vecchi file) mentre il file utilies vecchio non esisteva

def clean_dir ():

    curr_dir = os.getcwd()
    dir_to_clean = os.path.join(curr_dir,"static")
    for element in os.listdir(dir_to_clean):
        path = os.path.join(dir_to_clean,element)
        shutil.rmtree(path)

def create_idfolder():
    now = datetime.now()
    current_time = now.strftime("%H%M%S")
    id_folder = current_time + ''.join(random.choices(string.digits, k=10))
    return id_folder



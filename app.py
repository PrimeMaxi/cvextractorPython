from flask import Flask,request, jsonify
from werkzeug.utils import secure_filename

from extractdoc import extract_pdf

import os

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc'}

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/cvextractor', methods=['POST'])
def extract():
    if request.method == 'POST':

        file = request.files['file']
        file_name = secure_filename(file.filename)

        if file_name != '':

            split_tup = os.path.splitext(file_name)
            file_extension = split_tup[1]

            if file_extension in ALLOWED_EXTENSIONS:

                blocks = jsonify(extract_pdf(file))

                file.close()

                return blocks
            else:
                return "Upload file not correct, with extension '" + file_extension + "'. You can only upload files with this extension: " + str(
                    ALLOWED_EXTENSIONS)

        else:
            return "No upload file"


    else:
        return "Only method POST is available."

if __name__ == '__main__':
    app.run()

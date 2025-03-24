from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
from pdfparser import CVParser

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            parser = CVParser(filepath)
            result = parser.parse()
            return render_template('result.html', data=result)
        except Exception as e:
            return f"Error processing file: {str(e)}"
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    return 'Invalid file format'


if __name__ == '__main__':
    app.run(debug=True)

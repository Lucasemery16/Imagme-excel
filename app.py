from flask import Flask, render_template, request, send_file, jsonify
import os
import pandas as pd
from werkzeug.utils import secure_filename
import tempfile
import requests
import cv2
import numpy as np
import time
import easyocr
import re
from PIL import Image

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

reader = easyocr.Reader(['pt', 'en'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ocr_space_cell(image, api_key=None):
    result = reader.readtext(image, detail=0, paragraph=True)
    return ' '.join(result).strip()

def resize_image_if_needed(image_path, max_width=1000):
    img = Image.open(image_path)
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)
        img.save(image_path)

def extract_table(image_path):
    resize_image_if_needed(image_path)
    print(f"Processando imagem: {image_path}")
    img = cv2.imread(image_path, 0)
    img_bin = 255 - cv2.threshold(img, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    kernel_len = max(10, np.array(img).shape[1] // 40)
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    hor_lines = cv2.erode(img_bin, hor_kernel, iterations=3)
    hor_lines = cv2.dilate(hor_lines, hor_kernel, iterations=3)
    ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
    ver_lines = cv2.erode(img_bin, ver_kernel, iterations=3)
    ver_lines = cv2.dilate(ver_lines, ver_kernel, iterations=3)
    table_mask = cv2.addWeighted(hor_lines, 0.5, ver_lines, 0.5, 0.0)
    table_mask = cv2.erode(~table_mask, np.ones((3,3), np.uint8), iterations=2)
    _, table_mask = cv2.threshold(table_mask,128,255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(table_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cells = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 10 and h > 10:
            cells.append((x, y, w, h))
    print(f"Total de células detectadas: {len(cells)}")
    if not cells:
        raise Exception("Nenhuma célula de tabela detectada. Verifique a qualidade da imagem.")
    cells = sorted(cells, key=lambda b: (b[1], b[0]))
    # Agrupamento de linhas mais robusto
    rows = []
    current_row = []
    last_y = -1000
    tolerance = 15
    for cell in cells:
        x, y, w, h = cell
        if last_y == -1000 or abs(y - last_y) < tolerance:
            current_row.append(cell)
            last_y = y
        else:
            rows.append(sorted(current_row, key=lambda b: b[0]))
            current_row = [cell]
            last_y = y
    if current_row:
        rows.append(sorted(current_row, key=lambda b: b[0]))
    table_data = []
    img_color = cv2.imread(image_path)
    if len(cells) == 1:
        # Fallback: usa as coordenadas do EasyOCR para montar a tabela
        x, y, w, h = cells[0]
        cell_img = img_color[y:y+h, x:x+w]
        results = reader.readtext(cell_img, detail=1, paragraph=False)
        linhas = {}
        for bbox, text, conf in results:
            x_min = min([p[0] for p in bbox])
            y_min = min([p[1] for p in bbox])
            linha_key = int(y_min // 15)
            if linha_key not in linhas:
                linhas[linha_key] = []
            linhas[linha_key].append((x_min, text))
        for k in sorted(linhas.keys()):
            linha = [t[1] for t in sorted(linhas[k], key=lambda x: x[0])]
            table_data.append(linha)
    else:
        for row in rows:
            row_data = []
            for x, y, w, h in row:
                cell_img = img_color[y:y+h, x:x+w]
                start = time.time()
                text = ocr_space_cell(cell_img)
                elapsed = time.time() - start
                print(f"OCR célula: '{text}' (tempo: {elapsed:.2f}s)")
                row_data.append(text)
            table_data.append(row_data)
    return table_data

def images_to_excel_table(images, excel_path):
    # Para múltiplas imagens, empilha as tabelas verticalmente
    all_data = []
    for image_path in images:
        table = extract_table(image_path)
        all_data.extend(table)
    df = pd.DataFrame(all_data)
    df.to_excel(excel_path, index=False, header=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            if 'files' not in request.files:
                return jsonify({'error': 'Nenhum arquivo enviado!'}), 400
            files = request.files.getlist('files')
            image_paths = []
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(image_path)
                    image_paths.append(image_path)
            if not image_paths:
                return jsonify({'error': 'Nenhum arquivo válido enviado!'}), 400
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', dir=app.config['RESULT_FOLDER']) as tmp:
                excel_path = tmp.name
            images_to_excel_table(image_paths, excel_path)
            return send_file(excel_path, as_attachment=True, download_name='resultado_tabela.xlsx')
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) 
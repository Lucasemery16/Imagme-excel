from flask import Flask, request, send_file, jsonify, render_template
import os
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('home.html')



@app.route('/converter-txt', methods=['GET', 'POST'])
def converter_txt():
    resultado = None
    if request.method == 'POST':
        texto = request.form.get('texto', '').strip()
        if texto:
            convertido = texto.replace('.', ',')
            return render_template('converter_txt.html', resultado=convertido)
        if 'file' not in request.files:
            return render_template('converter_txt.html', resultado='Nenhum arquivo enviado ou texto colado!')
        file = request.files['file']
        if file.filename == '' or not file.filename.lower().endswith('.txt'):
            return render_template('converter_txt.html', resultado='Arquivo não suportado! Envie um .txt')
        conteudo = file.read().decode('utf-8')
        convertido = conteudo.replace('.', ',')
        return render_template('converter_txt.html', resultado=convertido)
    return render_template('converter_txt.html', resultado=resultado)

@app.route('/unificar-txt', methods=['GET', 'POST'])
def unificar_txt():
    if request.method == 'POST':
        if 'files' not in request.files:
            return 'Nenhum arquivo enviado!', 400
        files = request.files.getlist('files')
        conteudo_unificado = ''
        for file in files:
            if file and file.filename.lower().endswith('.txt'):
                conteudo_unificado += file.read().decode('utf-8') + '\n'
        if not conteudo_unificado.strip():
            return 'Nenhum arquivo .txt válido enviado!', 400
        conteudo_unificado = conteudo_unificado.replace('.', ',')
        from io import BytesIO
        return send_file(BytesIO(conteudo_unificado.encode('utf-8')),
                         as_attachment=True,
                         download_name='unificado.txt',
                         mimetype='text/plain')
    return render_template('unificar_txt.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 
from flask import Flask, request, send_file, jsonify, render_template
import os
import pandas as pd
import tempfile
import easyocr
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
reader = easyocr.Reader(['pt', 'en'])

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['GET'])
def upload_page():
    return render_template('index.html')

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

def corrigir_percentuais(texto):
    # Corrige casos de '3' no final de números para '%'
    texto = re.sub(r'(\d)3(?!\d)', r'\1%', texto)  # Ex: 1.0523 -> 1.052%
    texto = re.sub(r'(\d)\*', r'\1%', texto)       # Ex: 1.052* -> 1.052%
    texto = texto.replace(':', '%')
    return texto

def dividir_celula(celula):
    # Tenta dividir células grandes em várias colunas (números seguidos de % ou números)
    partes = re.findall(r'\d+[\.,]?\d*%?|[A-Za-zÀ-ÿ\-\/]+', celula)
    return [p for p in partes if p.strip()]

def corrigir_tabela(tabela):
    cabecalho = tabela[0]
    colunas = len(cabecalho)
    nova_tabela = [cabecalho]
    buffer_nome = ""
    for linha in tabela[1:]:
        linha_corrigida = []
        for cell in linha:
            cell = corrigir_percentuais(str(cell))
            partes = dividir_celula(cell)
            linha_corrigida.extend(partes)
        # Junta linhas de nomes
        if len(linha_corrigida) < colunas:
            buffer_nome += " " + " ".join(linha_corrigida)
        else:
            if buffer_nome:
                linha_corrigida[0] = buffer_nome.strip() + " " + linha_corrigida[0]
                buffer_nome = ""
            # Garante o número de colunas
            while len(linha_corrigida) < colunas:
                linha_corrigida.append("")
            while len(linha_corrigida) > colunas:
                linha_corrigida[-2] += " " + linha_corrigida[-1]
                linha_corrigida.pop()
            nova_tabela.append(linha_corrigida)
    return nova_tabela

@app.route('/imagem-para-json', methods=['POST'])
def imagem_para_json():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhuma imagem enviada!'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Arquivo vazio!'}), 400
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    result = reader.readtext(path, detail=1, paragraph=False)
    linhas = {}
    for bbox, texto, conf in result:
        y = int((bbox[0][1] + bbox[2][1]) / 2)
        linha_encontrada = False
        for key in linhas:
            if abs(key - y) < 15:
                linhas[key].append((bbox, texto))
                linha_encontrada = True
                break
        if not linha_encontrada:
            linhas[y] = [(bbox, texto)]
    tabela = []
    for key in sorted(linhas.keys()):
        linha = sorted(linhas[key], key=lambda x: x[0][0][0])
        tabela.append([t[1] for t in linha])
    tabela_corrigida = corrigir_tabela(tabela)
    return jsonify({'tabela': tabela_corrigida})

@app.route('/json-para-excel', methods=['POST'])
def json_para_excel():
    data = request.get_json()
    if not data or 'tabela' not in data:
        return jsonify({'error': 'JSON inválido!'}), 400
    tabela = data['tabela']
    df = pd.DataFrame(tabela)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        excel_path = tmp.name
    df.to_excel(excel_path, index=False, header=False)
    return send_file(excel_path, as_attachment=True, download_name='resultado_tabela.xlsx')

@app.route('/converter', methods=['GET'])
def converter_page():
    return render_template('converter.html')

def txt_para_tabela(txt):
    linhas = [l.strip() for l in txt.splitlines() if l.strip()]
    # Detecta o cabeçalho (primeira linha com mais de 3 colunas ou que contenha 'VaR' e 'Vol')
    for i, linha in enumerate(linhas):
        if ('VaR' in linha and 'Vol' in linha) or len(re.split(r'\s{2,}|\t|;', linha)) >= 4:
            header = re.split(r'\s{2,}|\t|;', linha)
            header_idx = i
            break
    else:
        return [], []
    dados = []
    buffer_nome = ""
    for linha in linhas[header_idx+1:]:
        partes = re.split(r'\s{2,}|\t|;', linha)
        # Se a linha tem menos colunas, provavelmente é parte do nome
        if len(partes) < len(header):
            buffer_nome += " " + " ".join(partes)
        else:
            if buffer_nome:
                partes[0] = buffer_nome.strip() + " " + partes[0]
                buffer_nome = ""
            # Garante o número de colunas
            while len(partes) < len(header):
                partes.append("")
            while len(partes) > len(header):
                partes[-2] += " " + partes[-1]
                partes.pop()
            dados.append(partes)
    return header, dados

@app.route('/txt-para-excel', methods=['POST'])
def txt_para_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado!'}), 400
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.txt'):
        return jsonify({'error': 'Arquivo não suportado! Envie um .txt'}), 400
    conteudo = file.read().decode('utf-8')
    # Processa o TXT para montar a tabela estruturada
    header, dados = txt_para_tabela(conteudo)
    if not header or not dados:
        return jsonify({'error': 'Não foi possível identificar a tabela no TXT.'}), 400
    import pandas as pd
    import tempfile
    df = pd.DataFrame(dados, columns=header)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        excel_path = tmp.name
    df.to_excel(excel_path, index=False)
    return send_file(excel_path, as_attachment=True, download_name='resultado_txt.xlsx')

@app.route('/txt-para-excel', methods=['GET'])
def txt_para_excel_page():
    return render_template('txt_para_excel.html')

def corrigir_percentuais_txt(linhas):
    novas_linhas = []
    for linha in linhas:
        partes = linha.split()
        nova_linha = []
        for parte in partes:
            # Corrige símbolos comuns no final
            parte_corrigida = re.sub(r'([\d,\.])[*:3]$', r'\1%', parte)
            # Se parece um percentual mas não termina com %, adiciona
            if re.match(r'^[\d,\.]+$', parte_corrigida) and len(parte_corrigida) > 1 and not parte_corrigida.endswith('%'):
                # Heurística: se valor entre 0 e 100, pode ser percentual
                try:
                    valor = float(parte_corrigida.replace(',', '.'))
                    if 0 <= valor <= 100:
                        parte_corrigida += '%'
                except:
                    pass
            nova_linha.append(parte_corrigida)
        novas_linhas.append(' '.join(nova_linha))
    return novas_linhas

@app.route('/imagem-para-txt', methods=['POST'])
def imagem_para_txt():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhuma imagem enviada!'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Arquivo vazio!'}), 400
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    result = reader.readtext(path, detail=0, paragraph=True)
    linhas_corrigidas = corrigir_percentuais_txt(result)
    texto = '\n'.join(linhas_corrigidas)
    from io import BytesIO
    return send_file(BytesIO(texto.encode('utf-8')),
                     as_attachment=True,
                     download_name='resultado_imagem.txt',
                     mimetype='text/plain')

@app.route('/imagem-para-txt', methods=['GET'])
def imagem_para_txt_page():
    return render_template('imagem_para_txt.html')

if __name__ == '__main__':
    app.run(debug=True) 
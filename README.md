# Conversores de TXT

Sistema simples para conversão e unificação de arquivos de texto (.txt).

## Funcionalidades

### 1. Converter TXT: Ponto para Vírgula
- Converte todos os pontos (.) em vírgulas (,) em arquivos .txt
- Suporta upload de arquivo ou colagem de texto
- Exibe o resultado para cópia ou download

### 2. Unificar TXT
- Combina múltiplos arquivos .txt em um único arquivo
- Converte pontos em vírgulas automaticamente
- Gera arquivo unificado para download

## Instalação Local

1. **Clone o repositório:**
```bash
git clone <url-do-repositorio>
cd converter-imagem-em-excel
```

2. **Crie e ative o ambiente virtual:**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

## Execução Local

1. **Ative o ambiente virtual:**
```bash
.venv\Scripts\activate  # Windows
```

2. **Execute o aplicativo:**
```bash
python app.py
```

3. **Acesse no navegador:**
```
http://localhost:5000
```

## Deploy no Render

O projeto está configurado para deploy automático no Render:

1. **Conecte seu repositório ao Render:**
   - Acesse [render.com](https://render.com)
   - Crie uma nova conta ou faça login
   - Clique em "New +" e selecione "Web Service"
   - Conecte seu repositório GitHub

2. **Configure o serviço:**
   - **Name**: `conversor-txt` (ou qualquer nome)
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Python Version**: `3.13.4`

3. **Deploy automático:**
   - O Render detectará automaticamente as configurações
   - Cada push para o branch `main` fará deploy automático
   - O serviço estará disponível em `https://seu-app.onrender.com`

### Configuração Automática

O arquivo `render.yaml` já está configurado para deploy automático. O Render usará essas configurações automaticamente.

## Estrutura do Projeto

```
├── app.py                 # Aplicação Flask principal
├── requirements.txt       # Dependências Python
├── templates/            # Templates HTML
│   ├── home.html         # Página inicial
│   ├── converter_txt.html # Conversor de TXT
│   └── unificar_txt.html # Unificador de TXT
├── uploads/              # Pasta para uploads temporários
└── results/              # Pasta para resultados
```

## Tecnologias Utilizadas

- **Flask**: Framework web Python
- **HTML/CSS**: Interface do usuário
- **JavaScript**: Interatividade do frontend

## Rotas da Aplicação

- `/`: Página inicial com links para as funcionalidades
- `/converter-txt`: Conversor de ponto para vírgula
- `/unificar-txt`: Unificador de arquivos TXT

## Como Usar

### Converter TXT
1. Acesse `/converter-txt`
2. Cole o texto ou faça upload de um arquivo .txt
3. Clique em "Converter"
4. Copie o resultado ou faça download

### Unificar TXT
1. Acesse `/unificar-txt`
2. Selecione múltiplos arquivos .txt
3. Clique em "Unificar Arquivos"
4. O arquivo unificado será baixado automaticamente 
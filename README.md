# Instalação e Dependências Necessárias
- pip install qrcode[pil]
- pip install pillow
- pip install opencv-python
- pip install unicodedata2

# Como Funciona o Sistema
O primeiro script serve para gerar os QR Codes de cada dog:

O QR Code contém:
- Nome do tutor
- Nome do dog
- Raça

O usuário deve enviar esses QR Codes para o celular
Assim ele poderá mostrar na frente da webcam para registrar a entrada.

# Registrar Entradas pela Webcam
O segundo script abre a webcam e fica lendo QR Codes.

Quando detecta um:
- Processa o conteúdo
- Impede duplicações no mesmo dia
- Registra no banco SQLite
- Emite um beep
- Para encerrar a leitura precione a tecla "q"

Atualiza automaticamente o CSV com chamada do dia

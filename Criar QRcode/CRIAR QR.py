import os
import qrcode
from PIL import Image, ImageDraw, ImageFont

def gerar_qr_code(nome_tutor, nome_dog, raca):
    qr_data = f"Tutor: {nome_tutor}\nDog: {nome_dog}\nRaça: {raca}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white').convert('RGB')

    texto = f"Tutor: {nome_tutor}  |  Dog: {nome_dog}  |  Raça: {raca}"
    try:
        fonte = ImageFont.truetype("arial.ttf", 20)
    except:
        fonte = ImageFont.load_default()

    bbox = fonte.getbbox(texto)
    largura_texto = bbox[2] - bbox[0]
    altura_texto = bbox[3] - bbox[1]

    largura_total = max(largura_texto, qr_img.width)
    altura_total = altura_texto + 20 + qr_img.height

    imagem_final = Image.new("RGB", (largura_total, altura_total), color="white")
    draw = ImageDraw.Draw(imagem_final)
    draw.text(((largura_total - largura_texto) // 2, 10), texto, font=fonte, fill="black")
    imagem_final.paste(qr_img, ((largura_total - qr_img.width) // 2, altura_texto + 20))

    nome_arquivo = f"{nome_tutor}{nome_dog}".replace(" ", "").replace("/", "-")
    img_path = f"banco_dados/qr_codes/{nome_arquivo}.png"
    imagem_final.save(img_path)
    print(f"\n✅ QR Code salvo em: {img_path}\n")

def main():
    os.makedirs('banco_dados/qr_codes', exist_ok=True)

    while True:
        nome_tutor = input("Nome do tutor: ")
        nome_dog = input("Nome do dog: ")
        raca = input("Raça do dog: ")

        gerar_qr_code(nome_tutor, nome_dog, raca)

        continuar = input("Deseja criar outro QR Code? (sim/não): ").strip().lower()
        if continuar != 'sim':
            break

if __name__ == "__main__":
    main()

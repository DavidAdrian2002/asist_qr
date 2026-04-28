import qrcode
import os
from PIL import Image, ImageDraw, ImageFont


def generar_qr(data, filename, nombre, apellido, dni=""):
    folder = "static/qr"

    if not os.path.exists(folder):
        os.makedirs(folder)

    # Crear QR
    qr = qrcode.make(data).convert("RGB")

    # Crear lienzo más grande
    ancho = 300
    alto = 420
    img = Image.new("RGB", (ancho, alto), "white")

    # Pegar QR centrado
    qr = qr.resize((220, 220))
    img.paste(qr, (40, 120))

    draw = ImageDraw.Draw(img)

    try:
        font_titulo = ImageFont.truetype("arial.ttf", 20)
        font_texto = ImageFont.truetype("arial.ttf", 16)
    except:
        font_titulo = ImageFont.load_default()
        font_texto = ImageFont.load_default()

    # Nombre
    nombre_completo = f"{nombre} {apellido}"
    draw.text((20, 20), nombre_completo, fill="black", font=font_titulo)

    # DNI
    if dni:
        draw.text((20, 60), f"DNI: {dni}", fill="black", font=font_texto)

    img.save(f"{folder}/{filename}.png")
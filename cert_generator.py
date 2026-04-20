from PIL import Image, ImageDraw, ImageFont
import qrcode
import io
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE_DIR, 'assets', 'base_template.png')
F_REG    = os.path.join(BASE_DIR, 'fonts', 'Cinzel-Regular.ttf')
F_BOLD   = os.path.join(BASE_DIR, 'fonts', 'Cinzel-Bold.ttf')

# Canvas 1600x900
W, H = 1600, 900
CX   = W // 2  # 800

# Posiciones para 1600x900
Y_NOMBRE  = 363
Y_BODY    = 455
LINE_GAP  = 26
Y_DATE    = 594
Y_CODE    = 803
QR_X, QR_Y, QR_SZ = 108, 87, 127
W_BODY_MAX = 1197

BLACK = (0, 0, 0, 255)
DARK  = (65, 65, 65, 255)


def fnt(path, size):
    return ImageFont.truetype(path, size)

def text_size(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2]-box[0], box[3]-box[1]

def draw_centered(draw, cx, y, text, font, color=BLACK):
    w, _ = text_size(draw, text, font)
    draw.text((cx - w // 2, y), text, font=font, fill=color)

def fit_name_font(draw, text, start=30, min_size=20, max_width=1300):
    for size in range(start, min_size - 1, -1):
        font = fnt(F_BOLD, size)
        if text_size(draw, text, font)[0] <= max_width:
            return font
    return fnt(F_BOLD, min_size)

def wrap_words(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        cand = f"{cur} {word}".strip()
        if text_size(draw, cand, font)[0] <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

def draw_body(draw, cx, y0, text, font, max_w, line_gap, color=DARK):
    lines = wrap_words(draw, text.upper(), font, max_w)
    y = y0
    for line in lines:
        draw_centered(draw, cx, y, line, font, color)
        y += line_gap

def make_qr(url, sz):
    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=6, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    return img.resize((sz, sz), Image.Resampling.LANCZOS)


def generate_certificate_bytes(nombre, horas, fecha, codigo, descripcion, url_qr=None):
    cert = Image.open(TEMPLATE).convert("RGBA")
    draw = ImageDraw.Draw(cert)

    # Fuentes
    fb = fnt(F_REG,  19)  # descripción
    fd = fnt(F_BOLD, 20)  # fecha
    fk = fnt(F_BOLD, 19)  # código

    # Nombre
    nombre_text = nombre.upper()
    fn = fit_name_font(draw, nombre_text)
    draw_centered(draw, CX, Y_NOMBRE, nombre_text, fn, BLACK)

    # Descripción
    body = descripcion.replace('{horas}', str(horas)) if '{horas}' in descripcion else descripcion
    draw_body(draw, CX, Y_BODY, body, fb, W_BODY_MAX, LINE_GAP, DARK)

    # Fecha
    draw_centered(draw, CX, Y_DATE, fecha, fd, BLACK)

    # Código
    draw_centered(draw, CX, Y_CODE, codigo, fk, BLACK)

    # QR
    if url_qr:
        qr_img = make_qr(url_qr, QR_SZ)
        cert.paste(qr_img, (QR_X, QR_Y), mask=qr_img)

    # Convertir a RGB y exportar como PNG en bytes
    final = Image.new("RGB", cert.size, (255, 255, 255))
    final.paste(cert, mask=cert.split()[3])
    buf = io.BytesIO()
    final.save(buf, format='PNG', dpi=(150, 150))
    return buf.getvalue()

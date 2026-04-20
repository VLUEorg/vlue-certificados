"""
Generador de certificados VLUE — versión servidor
Basado en el layout original (1510×1062), con isotipo, firmas y separador decorativo.
"""
from __future__ import annotations
import io
import os

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import qrcode

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE  = os.path.join(BASE_DIR, 'Certificado vacio.png')
REFERENCE = os.path.join(BASE_DIR, 'VLUE2025ACT0001.png')
ISOTIPO   = os.path.join(BASE_DIR, 'Isotipo Remastered.PNG')
GRADIENT  = os.path.join(BASE_DIR, 'gradient_strip.png')   # opcional
F_REG     = os.path.join(BASE_DIR, 'Cinzel-Regular.ttf')
F_BOLD    = os.path.join(BASE_DIR, 'Cinzel-Bold.ttf')
F_SEMI    = os.path.join(BASE_DIR, 'Cinzel-SemiBold.ttf')

# ── Colores ────────────────────────────────────────────────────────
BLACK = (0, 0, 0, 255)
GRAY  = (145, 145, 145, 255)
DARK  = (65, 65, 65, 255)

# ── Dimensiones y posiciones (template 1510×1062) ─────────────────
CX           = 755
X_L, X_R     = 380, 1143
LINE_HALF    = 158

LEFT_SIG_BOX     = (185, 726, 478, 834)
LEFT_SIG_SHIFT_X = 30

Y_VLUE   = 84;   FS_VLUE   = 26;  W_VLUE   = 105
Y_RUC    = 121;  FS_RUC    = 22;  W_RUC    = 405
Y_OTORGA = 174;  FS_OTORGA = 25;  W_OTORGA = 467
Y_CONST1 = 222;  FS_TITLE  = 60;  W_CONST1 = 657
Y_CONST2 = 290;                   W_CONST2 = 630
Y_APER   = 379;  FS_APER   = 27;  W_APER   = 285
Y_NOMBRE = 429;  FS_NOMBRE = 36
Y_LINE   = 504
Y_BODY   = 537;  FS_BODY   = 22;  W_BODY_MAX = 1130;  LINE_GAP = 31
Y_DATE   = 701;  FS_DATE   = 24
Y_ISO_CX = 843;  ISO_SZ    = 196
Y_SIGLINE = 817
Y_SNAME  = 839;  FS_SNAME  = 22
Y_SCARGO = 874;  FS_SCARGO = 24
Y_CODE   = 949;  FS_CODE   = 22
QR_X, QR_Y, QR_SZ = 102, 103, 150


# ── Helpers de texto ───────────────────────────────────────────────
def fnt(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)

def text_size(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]

def draw_centered(draw, cx, y, text, font, color=BLACK):
    w, _ = text_size(draw, text, font)
    draw.text((cx - w // 2, y), text, font=font, fill=color)

def fit_name_font(draw, text, start_size, min_size, max_width):
    for size in range(start_size, min_size - 1, -1):
        f = fnt(F_BOLD, size)
        if text_size(draw, text, f)[0] <= max_width:
            return f
    return fnt(F_BOLD, min_size)

def draw_spaced_to_width(draw, cx, y, text, font, target_w, color=BLACK):
    chars  = list(text)
    widths = [text_size(draw, c, font)[0] for c in chars]
    base   = sum(widths)
    n      = len(chars)
    gap    = (target_w - base) / (n - 1) if n > 1 and target_w > base else 0
    total  = base + gap * (n - 1)
    x      = cx - total / 2
    for c, w in zip(chars, widths):
        draw.text((round(x), y), c, font=font, fill=color)
        x += w + gap

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
    return y


# ── Separador decorativo ───────────────────────────────────────────
def gradient_separator(img: Image.Image, cx: int, y: int, xl: int, xr: int):
    # Extrae el separador desde el certificado bueno, no desde el template
    reference = Image.open(REFERENCE).convert('RGBA')
    crop = reference.crop((170, 500, 1374, 548))

    arr = np.array(crop)

    near_white = (arr[..., 0] > 245) & (arr[..., 1] > 245) & (arr[..., 2] > 245)
    arr[near_white, 3] = 0

    mask = arr[..., 3] > 0
    arr[..., 1] = np.where(mask, np.clip(arr[..., 1].astype(np.int16) + 6, 0, 255), arr[..., 1])
    arr[..., 2] = np.where(mask, np.clip(arr[..., 2].astype(np.int16) + 16, 0, 255), arr[..., 2])

    crop = Image.fromarray(arr)

    target_w = xr - xl
    target_h = 48
    crop = crop.resize((target_w, target_h), Image.Resampling.LANCZOS)

    img.alpha_composite(crop, (xl, y - target_h // 2))


# ── Isotipo ────────────────────────────────────────────────────────
def load_iso_transparent(path: str, size: int) -> Image.Image:
    im  = Image.open(path).convert('RGBA')
    arr = np.array(im)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    arr[(r < 45) & (g < 45) & (b < 45), 3] = 0
    ys, xs = np.where(arr[..., 3] > 10)
    if len(ys):
        arr = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return Image.fromarray(arr).resize((size, size), Image.Resampling.LANCZOS)


# ── QR ─────────────────────────────────────────────────────────────
def make_qr(url: str, sz: int) -> Image.Image:
    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=6, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white').convert('RGBA')
    return img.resize((sz, sz), Image.Resampling.LANCZOS)


# ── Función principal ──────────────────────────────────────────────
def generate_certificate_bytes(
    nombre: str,
    horas,
    fecha: str,
    codigo: str,
    descripcion: str,
    url_qr: str | None = None,
) -> bytes:
    """Genera el certificado y devuelve bytes PNG de alta calidad."""

    cert = Image.open(TEMPLATE).convert('RGBA')
    shift_left_signature(cert, LEFT_SIG_SHIFT_X)
    draw = ImageDraw.Draw(cert)

    # Fuentes
    fv = fnt(F_BOLD, FS_VLUE)
    fr = fnt(F_REG,  FS_RUC)
    fo = fnt(F_REG,  FS_OTORGA)
    ft = fnt(F_REG,  FS_TITLE)
    fa = fnt(F_REG,  FS_APER)
    fb = fnt(F_REG,  FS_BODY)
    fd = fnt(F_BOLD, FS_DATE)
    fs = fnt(F_BOLD, FS_SNAME)
    fc = fnt(F_BOLD, FS_SCARGO)
    fk = fnt(F_BOLD, FS_CODE)

    # Isotipo
    if os.path.exists(ISOTIPO):
        iso = load_iso_transparent(ISOTIPO, ISO_SZ)
        cert.paste(iso, (CX - ISO_SZ // 2, Y_ISO_CX - ISO_SZ // 2), mask=iso)

    # QR
    qr_url = url_qr or f'https://vlueorg.wixsite.com/my-site-1/verificar-certificados?codigo={codigo}'
    qr_img = make_qr(qr_url, QR_SZ)
    cert.paste(qr_img, (QR_X, QR_Y), mask=qr_img)

    draw = ImageDraw.Draw(cert)

    # Textos espaciados superiores
    draw_spaced_to_width(draw, CX, Y_VLUE,   'VLUE',                  fv, W_VLUE,   BLACK)
    draw_spaced_to_width(draw, CX, Y_RUC,    'RUC: 20614417570',      fr, W_RUC,    GRAY)
    draw_spaced_to_width(draw, CX, Y_OTORGA, 'SE OTORGA LA PRESENTE', fo, W_OTORGA, BLACK)
    draw_spaced_to_width(draw, CX, Y_CONST1, 'CONSTANCIA DE',         ft, W_CONST1, BLACK)
    draw_spaced_to_width(draw, CX, Y_CONST2, 'PARTICIPACIÓN',         ft, W_CONST2, BLACK)
    draw_spaced_to_width(draw, CX, Y_APER,   'A LA PERSONA',          fa, W_APER,   BLACK)

    # Nombre
    nombre_text = nombre.upper()
    fn     = fit_name_font(draw, nombre_text, FS_NOMBRE, FS_NOMBRE - 4, 980)
    name_w, _ = text_size(draw, nombre_text, fn)
    extra_gap  = 0
    if name_w > 900: extra_gap = 8
    if name_w > 960: extra_gap = 14
    draw_centered(draw, CX, Y_NOMBRE, nombre_text, fn, BLACK)

    # Separador decorativo
    gradient_separator(cert, CX, Y_LINE + extra_gap, 200, 1310)
    draw = ImageDraw.Draw(cert)

    # Descripción
    body = descripcion.replace('{horas}', str(horas)) if '{horas}' in descripcion else descripcion
    draw_body(draw, CX, Y_BODY + extra_gap, body, fb, W_BODY_MAX, LINE_GAP, DARK)

    # Fecha
    draw_centered(draw, CX, Y_DATE, fecha, fd, BLACK)

    # Líneas de firma
    for xc in (X_L, X_R):
        draw.line([(xc - LINE_HALF, Y_SIGLINE), (xc + LINE_HALF, Y_SIGLINE)],
                  fill=BLACK, width=2)

    # Nombres y cargos firmantes
    draw_centered(draw, X_L, Y_SNAME,  'SERGIO VALLEJOS',  fs, BLACK)
    draw_centered(draw, X_L, Y_SCARGO, 'PRESIDENTE',       fc, BLACK)
    draw_centered(draw, X_R, Y_SNAME,  'MIKEL CRUZALEGUI', fs, BLACK)
    draw_centered(draw, X_R, Y_SCARGO, 'SECRETARIO',       fc, BLACK)

    # Código
    draw_centered(draw, CX, Y_CODE, codigo, fk, BLACK)

    # Exportar PNG
    final = Image.new('RGB', cert.size, (255, 255, 255))
    final.paste(cert, mask=cert.split()[3])
    buf = io.BytesIO()
    final.save(buf, format='PNG', dpi=(150, 150))
    return buf.getvalue()


# ── Firma izquierda ────────────────────────────────────────────────
def shift_left_signature(cert: Image.Image, shift_x: int):
    x1, y1, x2, y2 = LEFT_SIG_BOX
    sig   = cert.crop((x1, y1, x2, y2))
    clear = Image.new('RGBA', (x2 - x1, y2 - y1), (255, 255, 255, 255))
    cert.paste(clear, (x1, y1))
    cert.paste(sig,   (x1 + shift_x, y1), mask=sig)

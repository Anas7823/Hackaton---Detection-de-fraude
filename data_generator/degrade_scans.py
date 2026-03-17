"""
Dégradation d'images pour simuler des scans de mauvaise qualité.
Applique rotation, flou, bruit, compression JPEG, etc.
"""

import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps


def degrade_image(
    input_path: Path,
    output_path: Path,
    severity: str = "random",
) -> str:
    """
    Dégrade une image pour simuler un scan réaliste.
    severity: 'light', 'medium', 'heavy', ou 'random'
    Retourne une description des dégradations appliquées.
    """
    if severity == "random":
        severity = random.choice(["light", "medium", "heavy"])

    img = Image.open(input_path).convert("RGB")
    applied = []

    if severity == "light":
        img, desc = _apply_light_degradation(img)
    elif severity == "medium":
        img, desc = _apply_medium_degradation(img)
    else:
        img, desc = _apply_heavy_degradation(img)
    applied.extend(desc)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if random.random() < 0.4:
        img.save(str(output_path), "JPEG", quality=random.randint(30, 60))
        applied.append("compression_jpeg")
    else:
        img.save(str(output_path), "PNG")

    return f"[{severity}] " + ", ".join(applied)


def _apply_light_degradation(img: Image.Image) -> tuple[Image.Image, list[str]]:
    applied = []

    angle = random.uniform(-2, 2)
    img = img.rotate(angle, expand=True, fillcolor=(255, 255, 255))
    applied.append(f"rotation({angle:.1f}°)")

    if random.random() < 0.5:
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        applied.append("flou_leger")

    brightness = random.uniform(0.9, 1.1)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    applied.append(f"luminosité({brightness:.2f})")

    return img, applied


def _apply_medium_degradation(img: Image.Image) -> tuple[Image.Image, list[str]]:
    applied = []

    angle = random.uniform(-5, 5)
    img = img.rotate(angle, expand=True, fillcolor=(245, 245, 240))
    applied.append(f"rotation({angle:.1f}°)")

    img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.8, 1.5)))
    applied.append("flou_moyen")

    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, random.uniform(5, 15), arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    applied.append("bruit_gaussien")

    contrast = random.uniform(0.7, 0.9)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    applied.append(f"contraste({contrast:.2f})")

    if random.random() < 0.4:
        img = ImageOps.grayscale(img).convert("RGB")
        applied.append("niveaux_de_gris")

    return img, applied


def _apply_heavy_degradation(img: Image.Image) -> tuple[Image.Image, list[str]]:
    applied = []

    angle = random.uniform(-10, 10)
    img = img.rotate(angle, expand=True, fillcolor=(240, 235, 230))
    applied.append(f"rotation({angle:.1f}°)")

    img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(1.5, 3.0)))
    applied.append("flou_fort")

    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, random.uniform(15, 30), arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    applied.append("bruit_fort")

    brightness = random.uniform(0.6, 0.8)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    applied.append(f"assombrissement({brightness:.2f})")

    contrast = random.uniform(0.5, 0.7)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    applied.append(f"contraste_faible({contrast:.2f})")

    if random.random() < 0.5:
        img = ImageOps.grayscale(img).convert("RGB")
        applied.append("niveaux_de_gris")

    if random.random() < 0.3:
        img = _add_stains(img)
        applied.append("taches")

    return img, applied


def _add_stains(img: Image.Image) -> Image.Image:
    """Ajoute des taches aléatoires simulant des marques de café/doigts."""
    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape[:2]

    for _ in range(random.randint(1, 4)):
        cx, cy = random.randint(0, w - 1), random.randint(0, h - 1)
        radius = random.randint(20, 80)
        y_coords, x_coords = np.ogrid[:h, :w]
        mask = ((x_coords - cx) ** 2 + (y_coords - cy) ** 2) <= radius ** 2
        stain_color = random.uniform(0.75, 0.92)
        arr[mask] = arr[mask] * stain_color

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def pdf_to_image(pdf_path: Path, dpi: int = 150) -> Path:
    """
    Convertit la première page d'un PDF en image PNG.
    Essaie pdf2image/poppler, puis pymupdf, sinon génère un rendu simplifié
    en extrayant le texte du PDF et en le dessinant sur une image blanche.
    """
    img_path = pdf_path.with_suffix(".png")

    try:
        from pdf2image import convert_from_path
        images = convert_from_path(str(pdf_path), dpi=dpi, first_page=1, last_page=1)
        if images:
            images[0].save(str(img_path), "PNG")
            return img_path
    except Exception:
        pass

    try:
        import fitz  # pymupdf
        doc = fitz.open(str(pdf_path))
        page = doc[0]
        pix = page.get_pixmap(dpi=dpi)
        pix.save(str(img_path))
        doc.close()
        return img_path
    except Exception:
        pass

    img = _render_pdf_text_to_image(pdf_path, dpi)
    img.save(str(img_path), "PNG")
    return img_path


def _render_pdf_text_to_image(pdf_path: Path, dpi: int) -> Image.Image:
    """Extrait le texte d'un PDF et le rend sur une image blanche."""
    from PIL import ImageDraw, ImageFont

    width = int(8.27 * dpi)
    height = int(11.69 * dpi)
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    text = ""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception:
        text = f"[Document: {pdf_path.name}]"

    if not text.strip():
        text = f"[Document: {pdf_path.name}]"

    try:
        font = ImageFont.truetype("arial.ttf", size=max(12, dpi // 12))
    except OSError:
        font = ImageFont.load_default()

    margin = int(dpi * 0.5)
    y = margin
    max_width = width - 2 * margin

    for line in text.split("\n"):
        if y > height - margin:
            break
        words = line.split()
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > max_width and current_line:
                draw.text((margin, y), current_line, fill="black", font=font)
                y += bbox[3] - bbox[1] + 4
                current_line = word
            else:
                current_line = test_line
        if current_line:
            bbox = draw.textbbox((0, 0), current_line, font=font)
            draw.text((margin, y), current_line, fill="black", font=font)
            y += bbox[3] - bbox[1] + 4

    return img

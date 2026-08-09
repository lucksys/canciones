#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>

<meta property="og:type" content="video.other">
<meta property="og:site_name" content="Google Drive">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="Haz clic para ver o escuchar la obra completa.">
<meta property="og:image" content="__IMAGE__">
<meta property="og:image:secure_url" content="__IMAGE__">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1168">
<meta property="og:image:height" content="784">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="__TITLE__">
<meta name="twitter:description" content="Haz clic para ver o escuchar la obra completa.">
<meta name="twitter:image" content="__IMAGE__">

<script>
const medias = {
  k: __URL_VIDEO_JS__,
  p: __URL_VIDEO_JS__,
  a: __URL_AUDIO_JS__
};

const params = new URLSearchParams(window.location.search);
const tipo = params.get("t");
const destino = medias[tipo] || medias.k;
window.location.replace(destino);
</script>

<style>
body {
  font-family: sans-serif;
  text-align: center;
  padding-top: 100px;
  background-color: #1a1a1a;
  color: #ffffff;
}
.loader {
  border: 4px solid #333;
  border-top: 4px solid #00ffcc;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 20px auto;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
a {
  color: #00ffcc;
  text-decoration: none;
  font-weight: bold;
}
</style>
</head>
<body>

<h2>Redirigiendo...</h2>
<div class="loader"></div>
<p>
  Si la redirección no funciona,
  <a href="__URL_VIDEO__">haz clic aquí</a>.
</p>

</body>
</html>
"""


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def slugify(text: str) -> str:
    text = strip_accents(text).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def normalize_key(text: str) -> str:
    return slugify(text).replace("_", "")


def print_help_and_exit(exit_code: int = 1) -> None:
    script = Path(sys.argv[0]).name or "generar_Index.py"
    print(
        f"""Uso:
  python {script} "Titulo" "portada.jpg" [--db Lista_de_Enlaces_de_Videos.txt]

Parámetros obligatorios:
  Titulo    : nombre de la obra, por ejemplo "Vinculo Sagrado"
  imagen    : archivo de imagen, por ejemplo "portada.jpg", "portada1.jpg", "portada2.jpg"

Parámetro opcional:
  --db      : archivo markdown de base de datos
              (por defecto: Lista_de_Enlaces_de_Videos.txt)

Ejemplos:
  python {script} "Vinculo Sagrado" portada.jpg
  python {script} "Personalidad y Esencia" portada1.jpg --db Lista_de_Enlaces_de_Videos.txt
"""
    )
    raise SystemExit(exit_code)


def parse_args() -> argparse.Namespace:
    # Mostrar ayuda si faltan parámetros obligatorios
    if len(sys.argv) < 3:
        print_help_and_exit(1)

    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("titulo", help='Título base, por ejemplo: "Vinculo Sagrado"')
    p.add_argument("imagen", help='Nombre de imagen, por ejemplo: portada.jpg, portada1.jpg, portada2.jpg')
    p.add_argument(
        "--db",
        default="Lista_de_Enlaces_de_Videos.txt",
        help="Ruta al archivo markdown de base de datos (por defecto: Lista_de_Enlaces_de_Videos.txt)"
    )
    return p.parse_args()


def split_blocks(md_text: str) -> List[List[str]]:
    blocks: List[List[str]] = []
    current: List[str] = []

    for raw in md_text.splitlines():
        line = raw.rstrip("\n")
        if re.match(r"^\s*\d+\s*-\s*", line):
            if current:
                blocks.append(current)
            current = [line]
        else:
            if current:
                current.append(line)

    if current:
        blocks.append(current)

    return blocks


def extract_value(line: str) -> str:
    m = re.match(r"^[^:]+:\s*\"?(.*?)\"?\s*$", line.strip())
    return m.group(1).strip() if m else ""


def parse_block(lines: List[str]) -> Optional[Dict[str, Any]]:
    if not lines:
        return None

    m = re.match(r"^\s*(\d+)\s*-\s*(.+)$", lines[0].strip())
    if not m:
        return None

    data: Dict[str, Any] = {
        "indice": int(m.group(1)),
        "titulo": m.group(2).replace("_", " ").strip(),
        "url_imagen": None,
        "url_video": None,
        "url_cancion": None,
        "info": "",
    }

    info_lines: List[str] = []
    in_info = False

    for line in lines[1:]:
        s = line.strip()
        if not s:
            if in_info:
                info_lines.append("")
            continue

        if re.match(r"^url-imagen\s*:", s, re.I):
            data["url_imagen"] = extract_value(s)
            in_info = False
        elif re.match(r"^url-video\s*:", s, re.I):
            data["url_video"] = extract_value(s)
            in_info = False
        elif re.match(r"^url-cancion\s*:", s, re.I):
            data["url_cancion"] = extract_value(s)
            in_info = False
        elif re.match(r"^info\s*:", s, re.I):
            in_info = True
            info_lines.append(extract_value(s))
        elif in_info:
            info_lines.append(s.strip('"'))

    data["info"] = "\n".join(info_lines).strip()

    if not data["url_imagen"] or not data["url_video"]:
        return None

    return data


def image_index_name(image_name: str) -> str:
    stem = Path(image_name).stem.lower()
    m = re.fullmatch(r"portada(\d*)", stem)
    if not m:
        raise ValueError(
            f"El nombre de imagen debe ser tipo portada.jpg, portada1.jpg, portada2.jpg... y se recibió: {image_name}"
        )
    suffix = m.group(1)
    return "index.html" if suffix == "" else f"index{suffix}.html"


def build_page_url(folder_slug: str, file_name: str) -> str:
    return f"https://lucksys.github.io/canciones/{folder_slug}/{file_name}"


def render_html(title: str, image_url: str, video_url: str, audio_url: str) -> str:
    page = HTML_TEMPLATE
    page = page.replace("__TITLE__", html.escape(title, quote=True))
    page = page.replace("__IMAGE__", html.escape(image_url, quote=True))
    page = page.replace("__URL_VIDEO__", html.escape(video_url, quote=True))
    page = page.replace("__URL_VIDEO_JS__", json.dumps(video_url))
    page = page.replace("__URL_AUDIO_JS__", json.dumps(audio_url))
    return page


def matches_target(entry: Dict[str, Any], target_title: str, target_image: str) -> bool:
    target_key = normalize_key(target_title)
    entry_key = normalize_key(entry["titulo"])
    image_basename = Path(str(entry["url_imagen"])).name.lower()
    return entry_key == target_key and image_basename == target_image.lower()


def main() -> int:
    args = parse_args()

    base_dir = Path(__file__).resolve().parent

    db_path = Path(args.db)
    if not db_path.is_absolute():
        db_path = (base_dir / db_path).resolve()

    if not db_path.is_file():
        raise FileNotFoundError(f"No se encontró la base de datos: {db_path}")

    titulo_base = args.titulo.strip()
    titulo1 = slugify(titulo_base)
    image_name = Path(args.imagen).name.lower()

    output_dir = base_dir / titulo1
    output_dir.mkdir(parents=True, exist_ok=True)

    index_name = image_index_name(image_name)

    md_text = db_path.read_text(encoding="utf-8")
    entries = [e for b in split_blocks(md_text) if (e := parse_block(b))]

    selected = [
        e for e in entries
        if matches_target(e, titulo_base, image_name)
    ]

    if not selected:
        print(f"No se encontró una entrada que coincida con título='{titulo_base}' e imagen='{image_name}'.")
        return 1

    entry = selected[0]

    URL_Raiz = f"https://lucksys.github.io/canciones/{titulo1}/"
    Url_Imagen = entry["url_imagen"]
    Url_Video = entry["url_video"]
    Url_Cancion = entry["url_cancion"] or entry["url_video"]
    Web_Video = f"{URL_Raiz}{index_name}?t=k"
    Web_Cancion = f"{URL_Raiz}{index_name}?t=a"
    Info = entry["info"]

    html_text = render_html(titulo_base, Url_Imagen, Url_Video, Url_Cancion)

    out_file = output_dir / index_name
    out_file.write_text(html_text, encoding="utf-8")

    print(f"Escrito: {out_file}")

    _ = {
        "Titulo": titulo_base,
        "Titulo1": titulo1,
        "URL_Raiz": URL_Raiz,
        "Url_Imagen": Url_Imagen,
        "Url_Video": Url_Video,
        "Url_Cancion": Url_Cancion,
        "Web_Video": Web_Video,
        "Web_Cancion": Web_Cancion,
        "Info": Info,
    }

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


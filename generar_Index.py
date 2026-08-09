#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_DB = "Lista_de_Enlaces_de_Videos.txt"
BASE_URL = "https://lucksys.github.io/canciones/"


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
    return "".join(
        ch for ch in normalized
        if not unicodedata.combining(ch)
    )


def slugify(text: str) -> str:
    text = strip_accents(text).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def normalize_db_text(text: str) -> str:
    return strip_accents(text).lower().strip()


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Genera index.html/index1.html/etc. para una obra "
            "y actualiza Lista_de_Enlaces_de_Videos.txt."
        ),
        epilog=(
            "Ejemplo para una entrada EXISTENTE:\n"
            '  ./generar_Index.py "Vinculo Sagrado" portada.jpg\n\n'
            "Ejemplo para una entrada NUEVA:\n"
            '  ./generar_Index.py "Nueva Cancion" portada.jpg '
            '"https://drive.google.com/file/d/VIDEO/view" '
            '"https://drive.google.com/file/d/AUDIO/view"\n\n'
            "Con otra base de datos:\n"
            '  ./generar_Index.py "Vinculo Sagrado" portada.jpg '
            '--db otra_base.txt'
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "titulo",
        nargs="?",
        help='Título de la obra. Ejemplo: "Vinculo Sagrado"',
    )

    parser.add_argument(
        "imagen",
        nargs="?",
        help="Nombre de imagen: portada.jpg, portada1.jpg, portada2.jpg, etc.",
    )

    parser.add_argument(
        "url_video",
        nargs="?",
        help="URL para la clave url-video: (necesaria solo para entradas nuevas).",
    )

    parser.add_argument(
        "url_cancion",
        nargs="?",
        help="URL para la clave url-cancion: (necesaria solo para entradas nuevas).",
    )

    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        help=f"Archivo de base de datos. Por defecto: {DEFAULT_DB}",
    )

    return parser


def split_blocks(md_text: str) -> List[List[str]]:

    blocks = []
    current = []

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

    m = re.match(
        r'^[^:]+:\s*"?(.+?)"?\s*$',
        line.strip()
    )

    return m.group(1).strip() if m else ""


def parse_block(lines: List[str]) -> Optional[Dict[str, Any]]:

    if not lines:
        return None

    m = re.match(
        r"^\s*(\d+)\s*-\s*(.+)$",
        lines[0].strip()
    )

    if not m:
        return None

    data = {
        "indice": int(m.group(1)),
        "titulo": m.group(2).replace("_", " ").strip(),
        "url_imagen": None,
        "url_video": None,
        "url_cancion": None,
        "info": "",
    }

    info_lines = []
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

        elif re.match(r"^url-canci[oó]n\s*:", s, re.I):

            data["url_cancion"] = extract_value(s)
            in_info = False

        elif re.match(r"^info\s*:", s, re.I):

            in_info = True
            info_lines.append(extract_value(s))

        elif in_info:

            info_lines.append(
                s.strip('"')
            )

    data["info"] = "\n".join(info_lines).strip()

    return data


def find_entry_span(
    lines: List[str],
    titulo: str
) -> Optional[tuple[int, int, int]]:

    target = slugify(titulo)

    header_pat = re.compile(
        r"^\s*(\d+)\s*-\s*(.+?)\s*$"
    )

    starts = []

    for i, line in enumerate(lines):

        m = header_pat.match(line)

        if m:

            starts.append(
                (
                    i,
                    int(m.group(1)),
                    slugify(m.group(2))
                )
            )

    for pos, (start, num, key) in enumerate(starts):

        if key == target:

            end = (
                starts[pos + 1][0]
                if pos + 1 < len(starts)
                else len(lines)
            )

            return start, end, num

    return None


def image_to_index_name(
    image_name: str
) -> tuple[str, str]:

    base = Path(image_name).name

    m = re.fullmatch(
        r"portada(\d*)\.jpg",
        base,
        re.I
    )

    if not m:

        raise ValueError(
            "El segundo parámetro debe ser "
            "portada.jpg, portada1.jpg, portada2.jpg, "
            "portada3.jpg, etc."
        )

    suffix = m.group(1)

    if suffix == "":
        return "index.html", "index"

    return (
        f"index{suffix}.html",
        f"index{suffix}"
    )


def build_urls(
    titulo1: str,
    web_name: str,
    title_has_public: bool
) -> tuple[str, str, str]:

    url_raiz = (
        f"{BASE_URL}{titulo1}/"
    )

    tipo = "p" if title_has_public else "k"

    web_url = (
        f"{url_raiz}"
        f"{web_name}"
        f"?t={tipo}&v=1"
    )

    return (
        url_raiz,
        web_url,
        web_url
    )


def find_key_index(
    block: List[str],
    key: str
) -> Optional[int]:

    target = normalize_db_text(key)

    for i, line in enumerate(block):

        if ":" not in line:
            continue

        current_key = normalize_db_text(
            line.split(":", 1)[0]
        )

        if current_key == target:
            return i

    return None


def upsert_line(
    block: List[str],
    key: str,
    value: str,
    after_keys: Optional[List[str]] = None
) -> None:

    after_keys = after_keys or []

    new_line = (
        f'{key}: "{value}"'
    )

    idx = find_key_index(
        block,
        key
    )

    if idx is not None:

        block[idx] = new_line
        return

    insert_at = 1

    for ak in after_keys:

        ak_idx = find_key_index(
            block,
            ak
        )

        if ak_idx is not None:

            insert_at = max(
                insert_at,
                ak_idx + 1
            )

    if insert_at > len(block):
        insert_at = len(block)

    block.insert(
        insert_at,
        new_line
    )


def ensure_info(
    block: List[str]
) -> None:

    if find_key_index(
        block,
        "info"
    ) is None:

        block.append(
            'info: "N.A."'
        )


def update_database_block(
    lines: List[str],
    start: int,
    end: int,
    url_imagen: str,
    web_video: str,
    web_cancion: str
) -> List[str]:

    block = lines[start:end]

    upsert_line(
        block,
        "url-imagen",
        url_imagen
    )

    upsert_line(
        block,
        "web-video",
        web_video,
        [
            "url-cancion",
            "url-video",
            "url-imagen"
        ]
    )

    upsert_line(
        block,
        "web-cancion",
        web_cancion,
        [
            "web-video",
            "url-cancion",
            "url-video",
            "url-imagen"
        ]
    )

    idx_video = find_key_index(
        block,
        "web-video"
    )

    idx_cancion = find_key_index(
        block,
        "web-cancion"
    )

    if (
        idx_video is not None
        and idx_cancion is not None
        and idx_cancion != idx_video + 1
    ):

        line_cancion = block.pop(
            idx_cancion
        )

        if idx_cancion < idx_video:
            idx_video -= 1

        block.insert(
            idx_video + 1,
            line_cancion
        )

    ensure_info(block)

    return (
        lines[:start]
        + block
        + lines[end:]
    )


def create_new_database_entry(
    md_text: str,
    titulo: str,
    url_imagen: str,
    url_video: str,
    url_cancion: str,
    web_video: str,
    web_cancion: str
) -> str:

    lines = md_text.splitlines()

    max_index = -1

    for line in lines:

        m = re.match(
            r"^\s*(\d+)\s*-\s*",
            line
        )

        if m:

            max_index = max(
                max_index,
                int(m.group(1))
            )

    new_index = max_index + 1

    entry = [
        "",
        "--------------------------------------------------------------------------------------------",
        f"{new_index}- {titulo}",
        "--------------------------------------------------------------------------------------------",
        "",
        f'url-imagen: "{url_imagen}"',
        f'url-video: "{url_video}"',
        f'url-cancion: "{url_cancion}"',
        f'web-video: "{web_video}"',
        f'web-cancion: "{web_cancion}"',
        'info: "N.A."',
        "",
    ]

    if not md_text.endswith("\n"):
        md_text += "\n"

    md_text += "\n".join(entry)

    return md_text


def render_html(
    title: str,
    image_url: str,
    video_url: str,
    audio_url: str
) -> str:

    page = HTML_TEMPLATE

    page = page.replace(
        "__TITLE__",
        html.escape(
            title,
            quote=True
        )
    )

    page = page.replace(
        "__IMAGE__",
        html.escape(
            image_url,
            quote=True
        )
    )

    page = page.replace(
        "__URL_VIDEO__",
        html.escape(
            video_url,
            quote=True
        )
    )

    page = page.replace(
        "__URL_VIDEO_JS__",
        json.dumps(video_url)
    )

    page = page.replace(
        "__URL_AUDIO_JS__",
        json.dumps(audio_url)
    )

    return page


def main() -> int:

    parser = build_parser()
    args = parser.parse_args()

    if not args.titulo or not args.imagen:

        parser.print_help()
        return 1

    titulo = args.titulo.strip()

    titulo1 = slugify(
        titulo
    )

    image_name = Path(
        args.imagen
    ).name

    base_dir = Path(
        __file__
    ).resolve().parent

    db_path = Path(
        args.db
    )

    if not db_path.is_absolute():

        db_path = (
            base_dir / db_path
        ).resolve()

    if not db_path.is_file():

        print(
            f"ERROR: No se encontró "
            f"la base de datos: {db_path}"
        )

        return 1

    try:

        html_name, web_name = (
            image_to_index_name(
                image_name
            )
        )

    except ValueError as e:

        print(
            f"ERROR: {e}"
        )

        return 1

    try:

        md_text = db_path.read_text(
            encoding="utf-8"
        )

    except Exception as e:

        print(
            f"ERROR leyendo la base de datos: {e}"
        )

        return 1

    lines = md_text.splitlines()

    found = find_entry_span(
        lines,
        titulo
    )

    titulo1_dir = (
        base_dir / titulo1
    )

    image_path = (
        titulo1_dir / image_name
    )

    # ---------------------------------------------------------
    # CASO 1:
    # La entrada YA existe en la base de datos.
    # ---------------------------------------------------------

    if found is not None:

        start, end, entry_number = found

        entry = parse_block(
            lines[start:end]
        )

        if entry is None:

            print(
                f'ERROR: No se pudo interpretar '
                f'la entrada "{titulo}".'
            )

            return 1

        if not entry["url_video"]:

            print(
                f'ERROR: La entrada "{titulo}" '
                f'no contiene la clave "url-video:".'
            )

            return 1

        if not entry["url_cancion"]:

            print(
                f'ERROR: La entrada "{titulo}" '
                f'no contiene la clave "url-cancion:".'
            )

            return 1

        url_video = entry["url_video"]
        url_cancion = entry["url_cancion"]

        title_has_public = (
            re.search(
                r"public",
                titulo,
                re.I
            )
            is not None
        )

        url_raiz = (
            f"{BASE_URL}{titulo1}/"
        )

        url_imagen = (
            f"{url_raiz}{image_name}"
        )

        _, web_video, web_cancion = (
            build_urls(
                titulo1,
                web_name,
                title_has_public
            )
        )

        updated_lines = update_database_block(
            lines,
            start,
            end,
            url_imagen,
            web_video,
            web_cancion
        )

        new_db_text = "\n".join(
            updated_lines
        )

        if md_text.endswith("\n"):
            new_db_text += "\n"

        try:

            db_path.write_text(
                new_db_text,
                encoding="utf-8"
            )

        except Exception as e:

            print(
                f"ERROR escribiendo la base de datos: {e}"
            )

            return 1

        print()
        print(
            f'Entrada existente actualizada: '
            f'"{titulo}"'
        )
        print(
            f"web-video  : {web_video}"
        )
        print(
            f"web-cancion: {web_cancion}"
        )

    # ---------------------------------------------------------
    # CASO 2:
    # La entrada NO existe.
    #
    # Para crearla son obligatorios:
    #   tercer parámetro = url-video
    #   cuarto parámetro = url-cancion
    #
    # Además debe existir la carpeta y la imagen.
    # ---------------------------------------------------------

    else:

        if not titulo1_dir.is_dir():

            print(
                f'ERROR: El título "{titulo}" '
                f'no existe en la base de datos y '
                f'no existe la carpeta: {titulo1_dir}'
            )

            return 1

        if not image_path.is_file():

            print(
                f'ERROR: El título "{titulo}" '
                f'no existe en la base de datos y '
                f'no existe la imagen: {image_path}'
            )

            return 1

        if not args.url_video:

            print(
                'ERROR: La entrada es nueva. '
                'Debe indicar el tercer parámetro '
                '"url-video".'
            )

            print()
            print(
                "Ejemplo:"
            )

            print(
                f'./generar_Index.py "{titulo}" '
                f'"{image_name}" '
                f'"https://drive.google.com/..." '
                f'"https://drive.google.com/..."'
            )

            return 1

        if not args.url_cancion:

            print(
                'ERROR: La entrada es nueva. '
                'Debe indicar el cuarto parámetro '
                '"url-cancion".'
            )

            print()
            print(
                "Ejemplo:"
            )

            print(
                f'./generar_Index.py "{titulo}" '
                f'"{image_name}" '
                f'"https://drive.google.com/VIDEO" '
                f'"https://drive.google.com/AUDIO"'
            )

            return 1

        url_video = args.url_video
        url_cancion = args.url_cancion

        title_has_public = (
            re.search(
                r"public",
                titulo,
                re.I
            )
            is not None
        )

        url_raiz = (
            f"{BASE_URL}{titulo1}/"
        )

        url_imagen = (
            f"{url_raiz}{image_name}"
        )

        _, web_video, web_cancion = (
            build_urls(
                titulo1,
                web_name,
                title_has_public
            )
        )

        new_db_text = (
            create_new_database_entry(
                md_text,
                titulo,
                url_imagen,
                url_video,
                url_cancion,
                web_video,
                web_cancion
            )
        )

        try:

            db_path.write_text(
                new_db_text,
                encoding="utf-8"
            )

        except Exception as e:

            print(
                f"ERROR escribiendo la base de datos: {e}"
            )

            return 1

        print()
        print(
            f'Nueva entrada creada al final de '
            f'"{db_path.name}": "{titulo}"'
        )
        print(
            f"url-imagen : {url_imagen}"
        )
        print(
            f"url-video  : {url_video}"
        )
        print(
            f"url-cancion: {url_cancion}"
        )
        print(
            f"web-video  : {web_video}"
        )
        print(
            f"web-cancion: {web_cancion}"
        )

    # ---------------------------------------------------------
    # Generación del HTML
    # ---------------------------------------------------------

    output_dir = (
        base_dir / titulo1
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    html_text = render_html(
        titulo,
        url_imagen,
        url_video,
        url_cancion
    )

    out_file = (
        output_dir / html_name
    )

    try:

        out_file.write_text(
            html_text,
            encoding="utf-8"
        )

    except Exception as e:

        print(
            f"ERROR escribiendo {out_file}: {e}"
        )

        return 1

    # ---------------------------------------------------------
    # Variables finales
    # ---------------------------------------------------------

    Titulo = titulo
    Titulo1 = titulo1
    URL_Raiz = url_raiz
    Url_Imagen = url_imagen
    Url_Video = url_video
    Url_Cancion = url_cancion
    Web_Video = web_video
    Web_Cancion = web_cancion

    print()
    print(
        "----------------------------------------"
    )
    print(
        "Generación completada correctamente."
    )
    print(
        "----------------------------------------"
    )
    print()
    print(
        f"Título       : {Titulo}"
    )
    print(
        f"Titulo1      : {Titulo1}"
    )
    print(
        f"Imagen       : {image_name}"
    )
    print(
        f"HTML         : {out_file}"
    )
    print()
    print(
        f"URL-Raíz     : {URL_Raiz}"
    )
    print(
        f"Url-Imagen   : {Url_Imagen}"
    )
    print(
        f"Url-Video    : {Url_Video}"
    )
    print(
        f"Url-Cancion  : {Url_Cancion}"
    )
    print(
        f"Web-Video    : {Web_Video}"
    )
    print(
        f"Web-Cancion  : {Web_Cancion}"
    )
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )

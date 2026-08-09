#!/usr/bin/env python3
from __future__ import annotations

import sys
import re
import html
import json
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

URL_RAIZ = "https://lucksys.github.io/canciones/"
DB_POR_DEFECTO = "Lista_de_Enlaces_de_Videos.txt"
SEPARADOR = "--------------------------------------------------------------------------------------------"


def mostrar_ayuda() -> None:
    print()
    print("Uso:")
    print()
    print('  ./generar_Index.py "Titulo"')
    print('  ./generar_Index.py "Titulo" "portada.jpg"')
    print('  ./generar_Index.py "Titulo" "portada.jpg" "URL-VIDEO" "URL-CANCION"')
    print('  ./generar_Index.py "Titulo" "portada.jpg" "URL-VIDEO" "URL-CANCION" --info "Texto opcional"')
    print()
    print("Reglas:")
    print("  - Si el título ya existe y tiene url-imagen, el segundo parámetro es opcional.")
    print("  - Si el título NO existe, son obligatorios:")
    print("      * título")
    print("      * imagen")
    print("    url-video y url-cancion pueden omitirse; en ese caso se guardan como \"\".")
    print("  - Si el título existe pero faltan url-video/url-cancion y no se pasan como parámetros,")
    print("    también se guardan como \"\".")
    print("  - --info es opcional y actualiza la clave info: dentro de la entrada.")
    print("  - --db es opcional y por defecto usa Lista_de_Enlaces_de_Videos.txt")
    print()
    print("Ejemplos:")
    print()
    print('  ./generar_Index.py "Vinculo Sagrado"')
    print('  ./generar_Index.py "Vinculo Sagrado" "portada.jpg"')
    print('  ./generar_Index.py "Nueva Obra" "portada.jpg" "https://video" "https://audio"')
    print('  ./generar_Index.py "Nueva Obra" "portada.jpg" "https://video" "https://audio" --info "Texto a probar"')
    print('  ./generar_Index.py "Nueva Obra" "portada.jpg" --info "Solo info"')
    print()
    sys.exit(0)


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def slugify(text: str) -> str:
    text = strip_accents(text).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def normalize_db_text(text: str) -> str:
    return strip_accents(text).lower().strip()


def titulo_subrayado(numero: int, titulo: str) -> str:
    encabezado = f"{numero}- {titulo}"
    return "-" * len(encabezado)


def separar_entradas(texto: str) -> List[str]:
    patron = r"(?m)(?=^\s*\d+\s*-\s*)"
    bloques = re.split(patron, texto)
    return [b for b in bloques if b.strip()]


def extraer_valor(linea: str) -> str:
    m = re.match(r'^\s*[^:]+:\s*"?(.+?)"?\s*$', linea.strip())
    return m.group(1).strip() if m else ""


def analizar_entrada(bloque: str) -> Dict[str, Any]:
    lineas = bloque.splitlines()
    titulo = None
    numero = None
    claves: Dict[str, str] = {}

    for linea in lineas:
        m = re.match(r"^\s*(\d+)\s*-\s*(.+?)\s*$", linea)
        if m:
            numero = int(m.group(1))
            titulo = m.group(2).strip().replace("_", " ")
            continue

        m = re.match(r"^\s*([A-Za-z0-9_-]+)\s*:", linea)
        if m:
            clave = normalize_db_text(m.group(1))
            claves[clave] = extraer_valor(linea)

    return {
        "numero": numero,
        "titulo": titulo,
        "claves": claves,
        "bloque": bloque,
    }


def buscar_entrada(entradas: List[Dict[str, Any]], titulo: str) -> Optional[Dict[str, Any]]:
    objetivo = titulo.strip().lower()
    for entrada in entradas:
        if entrada["titulo"] and entrada["titulo"].strip().lower() == objetivo:
            return entrada
    return None


def siguiente_indice(entradas: List[Dict[str, Any]]) -> int:
    nums = [e["numero"] for e in entradas if e["numero"] is not None]
    return (max(nums) + 1) if nums else 0


def image_to_index_name(image_name: str) -> Tuple[str, str]:
    base = Path(image_name).name
    m = re.fullmatch(r"portada(\d*)\.jpg", base, re.I)
    if not m:
        raise ValueError(
            'El nombre de imagen debe ser "portada.jpg", "portada1.jpg", "portada2.jpg", etc.'
        )
    numero = m.group(1)
    html_name = "index.html" if numero == "" else f"index{numero}.html"
    web_name = "index" if numero == "" else f"index{numero}"
    return html_name, web_name


def construir_url_imagen(titulo: str, nombre_imagen: str) -> str:
    titulo1 = slugify(titulo)
    return f"{URL_RAIZ}{titulo1}/{nombre_imagen}"


def construir_web_urls(titulo: str, web_name: str) -> Tuple[str, str]:
    titulo1 = slugify(titulo)
    modo = "p" if re.search(r"public", titulo, re.I) else "k"
    url = f"{URL_RAIZ}{titulo1}/{web_name}?t={modo}&v=1"
    return url, url


def find_key_index(block: List[str], key: str) -> Optional[int]:
    target = normalize_db_text(key)
    for i, line in enumerate(block):
        if ":" not in line:
            continue
        current_key = normalize_db_text(line.split(":", 1)[0])
        if current_key == target:
            return i
    return None


def eliminar_separadores_internos(block: List[str]) -> None:
    block[:] = [line for line in block if line.strip() != SEPARADOR]


def eliminar_separadores_finales(block: List[str]) -> None:
    while block and not block[-1].strip():
        block.pop()
    while block and re.fullmatch(r"-{20,}", block[-1].strip()):
        block.pop()
        while block and not block[-1].strip():
            block.pop()


def construir_bloque_ordenado(
    numero: int,
    titulo: str,
    url_imagen: str,
    url_video: str,
    url_cancion: str,
    web_video: str,
    web_cancion: str,
    info: str = "N.A.",
) -> List[str]:
    bloque = [
        f"{numero}- {titulo}",
        titulo_subrayado(numero, titulo),
        "",
        f'url-imagen: "{url_imagen}"',
        f'url-video: "{url_video}"',
        f'url-cancion: "{url_cancion}"',
        f'web-video: "{web_video}"',
        f'web-cancion: "{web_cancion}"',
        f'info: "{info}"',
        "",
        SEPARADOR,
    ]
    return bloque


def normalizar_bloque_existente(
    entrada: Dict[str, Any],
    titulo: str,
    nombre_imagen: Optional[str],
    url_video_param: Optional[str],
    url_cancion_param: Optional[str],
    info_param: Optional[str],
    web_video: str,
    web_cancion: str
) -> List[str]:
    numero = entrada["numero"]
    claves = entrada["claves"]

    if claves.get("url-imagen"):
        if nombre_imagen:
            url_imagen = construir_url_imagen(titulo, nombre_imagen)
        else:
            url_imagen = claves["url-imagen"]
    else:
        if not nombre_imagen:
            raise ValueError(
                'La entrada existe pero no tiene "url-imagen:"; debe indicarse el segundo parámetro (imagen).'
            )
        url_imagen = construir_url_imagen(titulo, nombre_imagen)

    url_video = (url_video_param if url_video_param is not None else claves.get("url-video", "")) or ""
    url_cancion = (url_cancion_param if url_cancion_param is not None else claves.get("url-cancion", "")) or ""
    info = (info_param if info_param is not None else claves.get("info", "N.A.")) or ""

    bloque = construir_bloque_ordenado(
        numero=numero,
        titulo=titulo,
        url_imagen=url_imagen,
        url_video=url_video,
        url_cancion=url_cancion,
        web_video=web_video,
        web_cancion=web_cancion,
        info=info,
    )

    eliminar_separadores_internos(bloque)
    eliminar_separadores_finales(bloque)

    if not bloque or bloque[-1].strip() != SEPARADOR:
        bloque.append(SEPARADOR)

    return bloque


def crear_bloque_nuevo(
    numero: int,
    titulo: str,
    nombre_imagen: str,
    url_video: str,
    url_cancion: str,
    info: str,
    web_video: str,
    web_cancion: str
) -> List[str]:
    url_imagen = construir_url_imagen(titulo, nombre_imagen)
    bloque = construir_bloque_ordenado(
        numero=numero,
        titulo=titulo,
        url_imagen=url_imagen,
        url_video=url_video,
        url_cancion=url_cancion,
        web_video=web_video,
        web_cancion=web_cancion,
        info=info,
    )
    eliminar_separadores_internos(bloque)
    eliminar_separadores_finales(bloque)
    if not bloque or bloque[-1].strip() != SEPARADOR:
        bloque.append(SEPARADOR)
    return bloque


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
const destino = medias[tipo] || medias.k || "";

if (destino) {
  window.location.replace(destino);
}
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


def render_html(title: str, image_url: str, video_url: str, audio_url: str) -> str:
    page = HTML_TEMPLATE
    page = page.replace("__TITLE__", html.escape(title, quote=True))
    page = page.replace("__IMAGE__", html.escape(image_url, quote=True))
    page = page.replace("__URL_VIDEO__", html.escape(video_url, quote=True))
    page = page.replace("__URL_VIDEO_JS__", json.dumps(video_url))
    page = page.replace("__URL_AUDIO_JS__", json.dumps(audio_url))
    return page


def build_parser():
    import argparse
    parser = argparse.ArgumentParser(
        description="Genera/actualiza index*.html y la base markdown para una obra.",
        epilog=(
            "Ejemplo:\n"
            '  ./generar_Index.py "Vinculo Sagrado"\n'
            '  ./generar_Index.py "Vinculo Sagrado" "portada.jpg"\n'
            '  ./generar_Index.py "Nueva Obra" "portada.jpg" "https://video" "https://audio"\n'
            '  ./generar_Index.py "Nueva Obra" "portada.jpg" "https://video" "https://audio" --info "Texto a probar"\n'
            '  ./generar_Index.py "Nueva Obra" "portada.jpg" --info "Solo info"'
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("titulo", nargs="?", help="Título de la obra")
    parser.add_argument("imagen", nargs="?", help="portada.jpg, portada1.jpg, portada2.jpg, ...")
    parser.add_argument("url_video", nargs="?", help="URL video (opcional)")
    parser.add_argument("url_cancion", nargs="?", help="URL canción (opcional)")
    parser.add_argument("--info", default=None, help='Texto opcional para la clave info: (por ejemplo "N.A." o una nota)')
    parser.add_argument("--db", default=DB_POR_DEFECTO, help="Archivo markdown de base de datos")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.titulo or len(sys.argv) == 1 or sys.argv[1] in ("-h", "--help"):
        mostrar_ayuda()

    titulo = args.titulo.strip()
    restantes = sys.argv[2:]

    db_path = Path(args.db)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path

    if not db_path.is_file():
        print(f"ERROR: No existe la base de datos: {db_path}")
        return 1

    texto = db_path.read_text(encoding="utf-8")
    entradas_raw = separar_entradas(texto)
    entradas = [analizar_entrada(b) for b in entradas_raw]

    entrada = buscar_entrada(entradas, titulo)
    titulo1 = slugify(titulo)
    carpeta_titulo = Path.cwd() / titulo1

    # ==================================================
    # CASO 1: EL TÍTULO YA EXISTE
    # ==================================================
    if entrada is not None:
        claves = entrada["claves"]

        if not claves.get("url-imagen") and len(restantes) < 1:
            print('ERROR: La entrada existe pero no tiene "url-imagen:"; debe indicarse el segundo parámetro.')
            return 1

        nombre_imagen = restantes[0] if restantes else None

        if nombre_imagen:
            if not carpeta_titulo.is_dir():
                print(f"ERROR: No existe la carpeta esperada: {carpeta_titulo}")
                return 1
            if not (carpeta_titulo / nombre_imagen).is_file():
                print(f"ERROR: No existe la imagen: {carpeta_titulo / nombre_imagen}")
                return 1
            imagen_usada = nombre_imagen
        else:
            imagen_usada = Path(claves["url-imagen"]).name if claves.get("url-imagen") else "portada.jpg"

        html_name, web_name = image_to_index_name(imagen_usada)
        web_video, web_cancion = construir_web_urls(titulo, web_name)

        url_video_param = restantes[1] if len(restantes) > 1 else None
        url_cancion_param = restantes[2] if len(restantes) > 2 else None

        nuevo_bloque = normalizar_bloque_existente(
            entrada=entrada,
            titulo=titulo,
            nombre_imagen=nombre_imagen,
            url_video_param=url_video_param,
            url_cancion_param=url_cancion_param,
            info_param=args.info,
            web_video=web_video,
            web_cancion=web_cancion,
        )

        reemplazo = "\n".join(nuevo_bloque) + "\n"
        texto_nuevo = texto.replace(entrada["bloque"], reemplazo, 1)
        db_path.write_text(texto_nuevo, encoding="utf-8")

        url_imagen = construir_url_imagen(titulo, imagen_usada)
        url_video = (url_video_param if url_video_param is not None else claves.get("url-video", "")) or ""
        url_cancion = (url_cancion_param if url_cancion_param is not None else claves.get("url-cancion", "")) or ""
        info_final = (args.info if args.info is not None else claves.get("info", "N.A.")) or ""

        carpeta_titulo.mkdir(parents=True, exist_ok=True)
        out_file = carpeta_titulo / html_name
        out_file.write_text(
            render_html(titulo, url_imagen, url_video, url_cancion),
            encoding="utf-8"
        )

        print()
        print("Entrada existente actualizada correctamente.")
        print(f"Título   : {titulo}")
        print(f"Imagen   : {imagen_usada}")
        print(f"Info     : {info_final}")
        print(f"HTML     : {out_file}")
        print(f"WebVideo : {web_video}")
        print(f"WebCanc. : {web_cancion}")
        print()

        return 0

    # ==================================================
    # CASO 2: EL TÍTULO NO EXISTE
    # ==================================================
    if len(restantes) < 1:
        print()
        print(f'ERROR: El título "{titulo}" no existe en la base de datos.')
        print("Para crear una nueva entrada necesitas al menos:")
        print('  1) imagen')
        print('Los campos url-video y url-cancion pueden omitirse; quedarán como "".')
        print()
        print("Ejemplo:")
        print(f'  ./generar_Index.py "{titulo}" "portada.jpg"')
        print(f'  ./generar_Index.py "{titulo}" "portada.jpg" "URL_VIDEO" "URL_CANCION" --info "Texto"')
        print()
        return 1

    nombre_imagen = restantes[0]
    url_video_param = restantes[1] if len(restantes) > 1 else ""
    url_cancion_param = restantes[2] if len(restantes) > 2 else ""

    if not carpeta_titulo.is_dir():
        print(f"ERROR: No existe la carpeta del título: {carpeta_titulo}")
        return 1

    if not (carpeta_titulo / nombre_imagen).is_file():
        print(f"ERROR: No existe la imagen: {carpeta_titulo / nombre_imagen}")
        return 1

    numero_nuevo = siguiente_indice(entradas)
    html_name, web_name = image_to_index_name(nombre_imagen)
    web_video, web_cancion = construir_web_urls(titulo, web_name)

    nuevo_bloque = crear_bloque_nuevo(
        numero=numero_nuevo,
        titulo=titulo,
        nombre_imagen=nombre_imagen,
        url_video=url_video_param,
        url_cancion=url_cancion_param,
        info=(args.info if args.info is not None else "N.A."),
        web_video=web_video,
        web_cancion=web_cancion,
    )

    texto = texto.rstrip("\n") + "\n" + "\n".join(nuevo_bloque) + "\n"
    db_path.write_text(texto, encoding="utf-8")

    url_imagen = construir_url_imagen(titulo, nombre_imagen)

    carpeta_titulo.mkdir(parents=True, exist_ok=True)
    out_file = carpeta_titulo / html_name
    out_file.write_text(
        render_html(titulo, url_imagen, url_video_param, url_cancion_param),
        encoding="utf-8"
    )

    print()
    print("Nueva entrada creada correctamente.")
    print(f"Indice   : {numero_nuevo}")
    print(f"Título   : {titulo}")
    print(f"Imagen   : {nombre_imagen}")
    print(f"Info     : {(args.info if args.info is not None else 'N.A.')}")
    print(f"HTML     : {out_file}")
    print(f"WebVideo : {web_video}")
    print(f"WebCanc. : {web_cancion}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

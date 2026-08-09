#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ============================================================
# CONFIGURACIÓN
# ============================================================

DEFAULT_DB = "Lista_de_Enlaces_de_Videos.txt"
BASE_URL = "https://lucksys.github.io/canciones/"


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def normalizar_titulo(titulo: str) -> str:
    """
    Convierte:
        Vinculo Sagrado
    en:
        vinculo_sagrado
    """
    return titulo.strip().lower().replace(" ", "_")


def obtener_indice_html(nombre_imagen: str) -> str:
    """
    Determina el nombre del archivo HTML a partir de la imagen.

    portada.jpg  -> index.html
    portada1.jpg -> index1.html
    portada2.jpg -> index2.html
    portada3.jpg -> index3.html
    """
    nombre = Path(nombre_imagen).name

    match = re.fullmatch(r"portada(\d*)\.jpg", nombre, re.IGNORECASE)

    if not match:
        raise ValueError(
            "El nombre de imagen debe tener el formato "
            "'portada.jpg', 'portada1.jpg', 'portada2.jpg', etc."
        )

    numero = match.group(1)

    if numero:
        return f"index{numero}.html"

    return "index.html"


def obtener_valor_clave(linea: str, clave: str) -> str | None:
    """
    Obtiene el valor de una clave del tipo:

    url-video: "https://..."
    """

    patron = rf"^\s*{re.escape(clave)}\s*:\s*\"([^\"]*)\""

    match = re.match(patron, linea, re.IGNORECASE)

    if match:
        return match.group(1).strip()

    return None


def encontrar_entrada(lineas: list[str], titulo: str):
    """
    Busca la entrada correspondiente al título.

    Ejemplo:

        Titulo recibido:
            Vinculo Sagrado

        Entrada:
            1- Vinculo_Sagrado

    Devuelve:
        inicio, fin, indice

    donde:
        inicio = primera línea de la entrada
        fin    = línea anterior a la siguiente entrada
    """

    titulo_normalizado = normalizar_titulo(titulo)

    patron_entrada = re.compile(
        r"^\s*(\d+)\s*-\s*(.+?)\s*$"
    )

    inicios = []

    for i, linea in enumerate(lineas):
        match = patron_entrada.match(linea)

        if match:
            numero = int(match.group(1))
            nombre = match.group(2).strip()

            nombre_normalizado = normalizar_titulo(nombre)

            inicios.append(
                (i, numero, nombre_normalizado)
            )

    for posicion, (inicio, numero, nombre_normalizado) in enumerate(inicios):

        if nombre_normalizado == titulo_normalizado:

            if posicion + 1 < len(inicios):
                fin = inicios[posicion + 1][0]
            else:
                fin = len(lineas)

            return inicio, fin, numero

    return None


def obtener_datos_entrada(
    lineas: list[str],
    inicio: int,
    fin: int
) -> dict[str, str | None]:

    datos = {
        "url-imagen": None,
        "url-video": None,
        "url-cancion": None,
        "web-video": None,
        "web-cancion": None,
        "info": None,
    }

    for i in range(inicio, fin):

        linea = lineas[i]

        for clave in datos:

            if re.match(
                rf"^\s*{re.escape(clave)}\s*:",
                linea,
                re.IGNORECASE
            ):
                datos[clave] = obtener_valor_clave(
                    linea,
                    clave
                )

    return datos


def construir_urls(titulo1: str, nombre_html: str):
    """
    Construye las URLs web correspondientes.

    Ejemplo:

    https://lucksys.github.io/canciones/
    vinculo_sagrado/
    index.html

    web-video:
        .../index.html?t=k

    web-cancion:
        .../index.html?t=a
    """

    url_raiz = BASE_URL + titulo1 + "/"

    url_base = url_raiz + nombre_html

    web_video = url_base + "?t=k"
    web_cancion = url_base + "?t=a"

    return url_raiz, web_video, web_cancion


# ============================================================
# ACTUALIZACIÓN DE LA BASE DE DATOS
# ============================================================

def actualizar_base_datos(
    lineas: list[str],
    inicio: int,
    fin: int,
    web_video: str,
    web_cancion: str
) -> list[str]:

    bloque = lineas[inicio:fin]

    indice_web_video = None
    indice_web_cancion = None

    for i, linea in enumerate(bloque):

        if re.match(
            r"^\s*web-video\s*:",
            linea,
            re.IGNORECASE
        ):
            indice_web_video = i

        elif re.match(
            r"^\s*web-cancion\s*:",
            linea,
            re.IGNORECASE
        ):
            indice_web_cancion = i

    nueva_linea_video = (
        f'web-video: "{web_video}"'
    )

    nueva_linea_cancion = (
        f'web-cancion: "{web_cancion}"'
    )

    # --------------------------------------------------------
    # Caso 1:
    # Existe web-video y web-cancion
    # --------------------------------------------------------

    if (
        indice_web_video is not None
        and indice_web_cancion is not None
    ):

        bloque[indice_web_video] = nueva_linea_video
        bloque[indice_web_cancion] = nueva_linea_cancion

        # Si por alguna razón web-cancion no está inmediatamente
        # debajo de web-video, se corrige su posición.
        if indice_web_cancion != indice_web_video + 1:

            del bloque[indice_web_cancion]

            if indice_web_cancion < indice_web_video:
                indice_web_video -= 1

            bloque.insert(
                indice_web_video + 1,
                nueva_linea_cancion
            )

    # --------------------------------------------------------
    # Caso 2:
    # Existe web-video pero no web-cancion
    # --------------------------------------------------------

    elif indice_web_video is not None:

        bloque[indice_web_video] = nueva_linea_video

        bloque.insert(
            indice_web_video + 1,
            nueva_linea_cancion
        )

    # --------------------------------------------------------
    # Caso 3:
    # No existe ninguna de las dos claves
    # --------------------------------------------------------

    else:

        posicion_insercion = None

        for i, linea in enumerate(bloque):

            if re.match(
                r"^\s*url-cancion\s*:",
                linea,
                re.IGNORECASE
            ):
                posicion_insercion = i + 1
                break

        if posicion_insercion is None:

            for i, linea in enumerate(bloque):

                if re.match(
                    r"^\s*url-video\s*:",
                    linea,
                    re.IGNORECASE
                ):
                    posicion_insercion = i + 1
                    break

        if posicion_insercion is None:
            posicion_insercion = len(bloque)

        bloque.insert(
            posicion_insercion,
            nueva_linea_video
        )

        bloque.insert(
            posicion_insercion + 1,
            nueva_linea_cancion
        )

    return lineas[:inicio] + bloque + lineas[fin:]


# ============================================================
# GENERACIÓN DEL INDEX.HTML
# ============================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>[Titulo]</title>

    <!-- Open Graph -->
    <meta property="og:type" content="video.other">
    <meta property="og:site_name" content="Google Drive">
    <meta property="og:title" content="[Titulo]">
    <meta property="og:description" content="Haz clic para ver o escuchar la obra completa.">

    <meta property="og:image" content="[URL-Imagen]">
    <meta property="og:image:secure_url" content="[URL-Imagen]">
    <meta property="og:image:type" content="image/jpeg">
    <meta property="og:image:width" content="1168">
    <meta property="og:image:height" content="784">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="[Titulo]">
    <meta name="twitter:description" content="Haz clic para ver o escuchar la obra completa.">
    <meta name="twitter:image" content="[URL-Imagen]">

    <script>
        const medias = {
            k: "[Url-Video]",
            p: "[Url-Video]",
            a: "[Url-Cancion]"
        };

        const params = new URLSearchParams(window.location.search);
        const tipo = params.get("t");

        // Video por defecto
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
        <a href="[Url-Video]">
            haz clic aquí
        </a>.
    </p>

</body>
</html>
"""


def generar_html(
    titulo: str,
    url_imagen: str,
    url_video: str,
    url_cancion: str
) -> str:

    html = HTML_TEMPLATE

    html = html.replace(
        "[Titulo]",
        titulo
    )

    html = html.replace(
        "[URL-Imagen]",
        url_imagen
    )

    html = html.replace(
        "[Url-Video]",
        url_video
    )

    html = html.replace(
        "[Url-Cancion]",
        url_cancion
    )

    return html


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Genera index.html/index1.html/etc. para una obra "
            "y actualiza web-video y web-cancion en "
            "Lista_de_Enlaces_de_Videos.txt."
        ),
        epilog=(
            "Ejemplo:\n"
            "  ./generar_Index.py \"Vinculo Sagrado\" portada.jpg\n\n"
            "Con una base de datos diferente:\n"
            "  ./generar_Index.py \"Vinculo Sagrado\" "
            "portada.jpg --db otra_base.txt"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "titulo",
        nargs="?",
        help="Título de la obra. Ejemplo: \"Vinculo Sagrado\""
    )

    parser.add_argument(
        "imagen",
        nargs="?",
        help=(
            "Nombre de la imagen: portada.jpg, "
            "portada1.jpg, portada2.jpg, etc."
        )
    )

    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        help=(
            "Archivo de base de datos. "
            f"Por defecto: {DEFAULT_DB}"
        )
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Comprobación de parámetros
    # --------------------------------------------------------

    if not args.titulo or not args.imagen:

        parser.print_help()
        return 1

    titulo = args.titulo.strip()
    nombre_imagen = Path(args.imagen).name

    # --------------------------------------------------------
    # Directorio raíz del proyecto
    # --------------------------------------------------------

    directorio_script = Path(__file__).resolve().parent

    archivo_db = Path(args.db)

    if not archivo_db.is_absolute():
        archivo_db = directorio_script / archivo_db

    if not archivo_db.exists():

        print(
            f"ERROR: No existe la base de datos:\n"
            f"{archivo_db}"
        )

        return 1

    # --------------------------------------------------------
    # Titulo1
    # --------------------------------------------------------

    titulo1 = normalizar_titulo(titulo)

    # --------------------------------------------------------
    # Nombre del HTML
    # --------------------------------------------------------

    try:

        nombre_html = obtener_indice_html(
            nombre_imagen
        )

    except ValueError as e:

        print(f"ERROR: {e}")

        return 1

    # --------------------------------------------------------
    # Leer base de datos
    # --------------------------------------------------------

    try:

        contenido = archivo_db.read_text(
            encoding="utf-8"
        )

    except Exception as e:

        print(
            f"ERROR leyendo la base de datos: {e}"
        )

        return 1

    lineas = contenido.splitlines()

    # --------------------------------------------------------
    # Buscar entrada correspondiente
    # --------------------------------------------------------

    resultado = encontrar_entrada(
        lineas,
        titulo
    )

    if resultado is None:

        print(
            f'ERROR: No se encontró la entrada '
            f'"{titulo}" en {archivo_db.name}.'
        )

        return 1

    inicio, fin, numero = resultado

    # --------------------------------------------------------
    # Obtener datos existentes
    # --------------------------------------------------------

    datos = obtener_datos_entrada(
        lineas,
        inicio,
        fin
    )

    url_imagen = datos["url-imagen"]
    url_video = datos["url-video"]
    url_cancion = datos["url-cancion"]

    if not url_imagen:

        print(
            f'ERROR: La entrada "{titulo}" '
            f'no contiene la clave "url-imagen:".'
        )

        return 1

    if not url_video:

        print(
            f'ERROR: La entrada "{titulo}" '
            f'no contiene la clave "url-video:".'
        )

        return 1

    if not url_cancion:

        print(
            f'ERROR: La entrada "{titulo}" '
            f'no contiene la clave "url-cancion:".'
        )

        return 1

    # --------------------------------------------------------
    # Construir URLs web
    # --------------------------------------------------------

    url_raiz, web_video, web_cancion = construir_urls(
        titulo1,
        nombre_html
    )

    # --------------------------------------------------------
    # Actualizar base de datos
    # --------------------------------------------------------

    nuevas_lineas = actualizar_base_datos(
        lineas,
        inicio,
        fin,
        web_video,
        web_cancion
    )

    nuevo_contenido = "\n".join(
        nuevas_lineas
    )

    if contenido.endswith("\n"):
        nuevo_contenido += "\n"

    try:

        archivo_db.write_text(
            nuevo_contenido,
            encoding="utf-8"
        )

    except Exception as e:

        print(
            f"ERROR escribiendo la base de datos: {e}"
        )

        return 1

    # --------------------------------------------------------
    # Directorio de la obra
    # --------------------------------------------------------

    directorio_obra = (
        directorio_script / titulo1
    )

    directorio_obra.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Generar HTML
    # --------------------------------------------------------

    html = generar_html(
        titulo,
        url_imagen,
        url_video,
        url_cancion
    )

    archivo_html = (
        directorio_obra / nombre_html
    )

    try:

        archivo_html.write_text(
            html,
            encoding="utf-8"
        )

    except Exception as e:

        print(
            f"ERROR escribiendo {archivo_html}: {e}"
        )

        return 1

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print()
    print("Generación completada correctamente.")
    print()
    print(f"Título       : {titulo}")
    print(f"Titulo1      : {titulo1}")
    print(f"Imagen       : {nombre_imagen}")
    print(f"HTML         : {archivo_html}")
    print()
    print(f"URL-Raíz     : {url_raiz}")
    print(f"web-video    : {web_video}")
    print(f"web-cancion  : {web_cancion}")
    print()
    print(
        f'Entrada actualizada: {numero}- {titulo}'
    )
    print(
        'web-video: y web-cancion: quedaron '
        'consecutivas.'
    )
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


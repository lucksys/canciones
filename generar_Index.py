#!/usr/bin/env python3
from __future__ import annotations

import sys
import re
import html
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


URL_RAIZ = "https://lucksys.github.io/canciones/"
DB_POR_DEFECTO = "Lista_de_Enlaces_de_Videos.txt"
SEPARADOR = "--------------------------------------------------------------------------------------------"


# ============================================================
# AYUDA
# ============================================================

def mostrar_ayuda() -> None:
    print()
    print("Uso:")
    print()
    print('  ./generar_Index.py "Titulo"')
    print('  ./generar_Index.py "Titulo" "portada.jpg"')
    print('  ./generar_Index.py "Titulo" "portada.jpg" "URL-VIDEO" "URL-CANCION"')
    print('  ./generar_Index.py "Titulo" "portada.jpg" "URL-VIDEO" "URL-CANCION" --info "Texto"')
    print()
    print("Reglas:")
    print()
    print("  - El título completo identifica UNA entrada concreta.")
    print("  - El nombre del directorio se obtiene del título base.")
    print("  - En títulos con variante final entre paréntesis, se elimina")
    print("    solamente el sufijo _(....) para obtener el directorio.")
    print("  - El directorio conserva comas, acentos y demás caracteres.")
    print("  - Los espacios del directorio se convierten en '_'.")
    print("  - El directorio se convierte a minúsculas.")
    print()
    print("  - Si la entrada ya existe:")
    print("      * imagen es opcional si ya existe url-imagen:")
    print("      * url-video es opcional")
    print("      * url-cancion es opcional")
    print("      * --info es opcional")
    print()
    print("  - Si url-video o url-cancion no existen y tampoco se proporcionan,")
    print('    se guardan como "".')
    print()
    print("  - Las claves siempre quedan en este orden:")
    print("      url-imagen:")
    print("      url-video:")
    print("      url-cancion:")
    print("      web-video:")
    print("      web-cancion:")
    print("      info:")
    print()
    print("  - Nunca se coloca el separador dentro de una entrada.")
    print("  - Cada entrada termina con:")
    print(f"      {SEPARADOR}")
    print("    seguido obligatoriamente por un carácter de nueva línea.")
    print()
    print("  - web-video termina siempre en:")
    print("      ?t=k&v=1")
    print()
    print("  - web-cancion termina siempre en:")
    print("      ?t=a&v=1")
    print()
    print("Ejemplos:")
    print()
    print('  ./generar_Index.py "Vinculo Sagrado"')
    print()
    print('  ./generar_Index.py "Vinculo Sagrado" "portada.jpg"')
    print()
    print('  ./generar_Index.py "Nueva Obra" "portada.jpg" "https://video" "https://audio"')
    print()
    print('  ./generar_Index.py "Nueva Obra" "portada.jpg" "https://video" "https://audio" --info "Texto a probar"')
    print()
    print('  ./generar_Index.py "Nueva Obra" "portada.jpg" --info "Solo información"')
    print()
    sys.exit(0)


# ============================================================
# NORMALIZACIÓN DEL TÍTULO
# ============================================================

def slugify(text: str) -> str:
    """
    Se mantiene para otras operaciones internas que necesiten
    comparación normalizada.

    NO se utiliza para determinar el nombre físico del directorio.
    """
    import unicodedata

    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(
        ch for ch in normalized
        if not unicodedata.combining(ch)
    )

    normalized = normalized.lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized.strip("_")


def normalize_db_text(text: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(
        ch for ch in normalized
        if not unicodedata.combining(ch)
    )

    return normalized.lower().strip()


def titulo_base_directorio(titulo: str) -> str:
    """
    Obtiene EXACTAMENTE el nombre base utilizado para el directorio.

    IMPORTANTE:
    NO utiliza slugify(), porque eso destruiría la compatibilidad
    con directorios existentes que contienen coma o acentos.

    Ejemplos:

        1717, Una Conspiración del Alma
        ->
        1717,_una_conspiración_del_alma

        Personalidad_y_Esencia_(EPIC)
        ->
        personalidad_y_esencia

        Personalidad_y_Esencia_(Personalitá e Essenza Italiano)
        ->
        personalidad_y_esencia

    Reglas:

        1. Elimina solamente el sufijo final _(....)
        2. Conserva comas
        3. Conserva acentos
        4. Convierte espacios en "_"
        5. Reduce "_" consecutivos
        6. Convierte todo a minúsculas
    """

    base = titulo.strip()

    # Elimina únicamente la variante final:
    #
    # Personalidad_y_Esencia_(EPIC)
    #                         ^^^^^^
    #
    # queda:
    #
    # Personalidad_y_Esencia
    #
    base = re.sub(
        r"_\([^()]*\)\s*$",
        "",
        base
    )

    # Espacios -> "_"
    base = re.sub(
        r"\s+",
        "_",
        base
    )

    # Evita "_" duplicados
    base = re.sub(
        r"_+",
        "_",
        base
    )

    # IMPORTANTE:
    # NO eliminar comas.
    # NO eliminar acentos.
    # NO pasar por slugify().
    return base.lower()


# ============================================================
# BASE DE DATOS
# ============================================================

def separar_entradas(texto: str) -> List[str]:
    """
    Separa las entradas mediante el número inicial.

    Ejemplo:

    0- Titulo
    ...
    --------------------------------------------------------------------------------------------

    1- Otro Titulo
    ...
    """

    patron = r"(?m)(?=^\s*\d+\s*-\s*)"

    bloques = re.split(
        patron,
        texto
    )

    return [
        bloque
        for bloque in bloques
        if bloque.strip()
    ]


def extraer_valor(linea: str) -> str:
    """
    Extrae el contenido de:

        clave: "valor"

    """

    m = re.match(
        r'^\s*[^:]+:\s*"?(.+?)"?\s*$',
        linea.strip()
    )

    return m.group(1).strip() if m else ""


def analizar_entrada(
    bloque: str
) -> Dict[str, Any]:

    lineas = bloque.splitlines()

    titulo = None
    numero = None
    claves: Dict[str, str] = {}

    for linea in lineas:

        m = re.match(
            r"^\s*(\d+)\s*-\s*(.+?)\s*$",
            linea
        )

        if m:

            numero = int(m.group(1))

            titulo = (
                m.group(2)
                .strip()
                .replace("_", " ")
            )

            continue

        m = re.match(
            r"^\s*([A-Za-z0-9_-]+)\s*:",
            linea
        )

        if m:

            clave = normalize_db_text(
                m.group(1)
            )

            claves[clave] = extraer_valor(linea)

    return {
        "numero": numero,
        "titulo": titulo,
        "claves": claves,
        "bloque": bloque,
    }


def buscar_entrada(
    entradas: List[Dict[str, Any]],
    titulo: str
) -> Optional[Dict[str, Any]]:

    objetivo = titulo.strip().lower()

    for entrada in entradas:

        titulo_entrada = entrada["titulo"]

        if titulo_entrada is None:
            continue

        if titulo_entrada.strip().lower() == objetivo:
            return entrada

    return None


def siguiente_indice(
    entradas: List[Dict[str, Any]]
) -> int:

    numeros = [
        entrada["numero"]
        for entrada in entradas
        if entrada["numero"] is not None
    ]

    return (
        max(numeros) + 1
        if numeros
        else 0
    )


# ============================================================
# IMÁGENES / INDEX
# ============================================================

def obtener_numero_index(
    nombre_imagen: str
) -> str:

    base = Path(nombre_imagen).name

    m = re.fullmatch(
        r"portada(\d*)\.jpg",
        base,
        re.I
    )

    if not m:

        raise ValueError(
            'El nombre de imagen debe ser '
            '"portada.jpg", "portada1.jpg", '
            '"portada2.jpg", etc.'
        )

    return m.group(1)


def image_to_index_name(
    image_name: str
) -> Tuple[str, str]:

    numero = obtener_numero_index(
        image_name
    )

    html_name = (
        "index.html"
        if numero == ""
        else f"index{numero}.html"
    )

    web_name = (
        "index"
        if numero == ""
        else f"index{numero}"
    )

    return html_name, web_name


# ============================================================
# URL
# ============================================================

def construir_url_imagen(
    titulo: str,
    nombre_imagen: str
) -> str:

    titulo1 = titulo_base_directorio(
        titulo
    )

    return (
        f"{URL_RAIZ}"
        f"{titulo1}/"
        f"{nombre_imagen}"
    )


def construir_web_urls(
    titulo: str,
    web_name: str
) -> Tuple[str, str]:

    titulo1 = titulo_base_directorio(
        titulo
    )

    web_video = (
        f"{URL_RAIZ}"
        f"{titulo1}/"
        f"{web_name}"
        f"?t=k&v=1"
    )

    web_cancion = (
        f"{URL_RAIZ}"
        f"{titulo1}/"
        f"{web_name}"
        f"?t=a&v=1"
    )

    return (
        web_video,
        web_cancion
    )


# ============================================================
# CONSTRUCCIÓN DE ENTRADAS
# ============================================================

def titulo_subrayado(
    numero: int,
    titulo: str
) -> str:

    encabezado = (
        f"{numero}- {titulo}"
    )

    return "-" * len(encabezado)


def eliminar_separadores_internos(
    bloque: List[str]
) -> None:

    bloque[:] = [
        linea
        for linea in bloque
        if linea.strip() != SEPARADOR
    ]


def eliminar_separadores_finales(
    bloque: List[str]
) -> None:

    while (
        bloque
        and not bloque[-1].strip()
    ):
        bloque.pop()

    while (
        bloque
        and re.fullmatch(
            r"-{20,}",
            bloque[-1].strip()
        )
    ):

        bloque.pop()

        while (
            bloque
            and not bloque[-1].strip()
        ):
            bloque.pop()


def construir_bloque_ordenado(
    numero: int,
    titulo: str,
    url_imagen: str,
    url_video: str,
    url_cancion: str,
    web_video: str,
    web_cancion: str,
    info: str = "N.A."
) -> List[str]:

    bloque = [

        f"{numero}- {titulo}",

        titulo_subrayado(
            numero,
            titulo
        ),

        "",
        f'url-imagen:  "{url_imagen}"',
        f'url-video:   "{url_video}"',
        f'url-cancion: "{url_cancion}"',
        f'web-video:   "{web_video}"',
        f'web-cancion: "{web_cancion}"',
        f'info:        "{info}"',
        "\n",

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

    # --------------------------------------------------------
    # URL IMAGEN
    # --------------------------------------------------------

    if claves.get("url-imagen"):

        if nombre_imagen:

            url_imagen = construir_url_imagen(
                titulo,
                nombre_imagen
            )

        else:

            url_imagen = claves["url-imagen"]

    else:

        if not nombre_imagen:

            raise ValueError(
                'La entrada existe pero no tiene '
                '"url-imagen:"; debe indicarse '
                'el segundo parámetro (imagen).'
            )

        url_imagen = construir_url_imagen(
            titulo,
            nombre_imagen
        )

    # --------------------------------------------------------
    # URL VIDEO
    # --------------------------------------------------------

    if url_video_param is not None:

        url_video = url_video_param

    else:

        url_video = claves.get(
            "url-video",
            ""
        )

    if url_video is None:
        url_video = ""

    # --------------------------------------------------------
    # URL CANCION
    # --------------------------------------------------------

    if url_cancion_param is not None:

        url_cancion = url_cancion_param

    else:

        url_cancion = claves.get(
            "url-cancion",
            ""
        )

    if url_cancion is None:
        url_cancion = ""

    # --------------------------------------------------------
    # INFO
    # --------------------------------------------------------

    if info_param is not None:

        info = info_param

    else:

        info = claves.get(
            "info",
            "N.A."
        )

    if info is None:
        info = ""

    # --------------------------------------------------------
    # RECONSTRUCCIÓN COMPLETA
    #
    # Esto garantiza SIEMPRE el orden correcto.
    # --------------------------------------------------------

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

    # Nunca debe existir un separador dentro
    # del contenido de una entrada.

    eliminar_separadores_internos(
        bloque
    )

    # Eliminamos cualquier separador final
    # para reconstruirlo correctamente.

    eliminar_separadores_finales(
        bloque
    )

    # Separador final obligatorio.

    bloque.append(
        SEPARADOR
    )

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

    url_imagen = construir_url_imagen(
        titulo,
        nombre_imagen
    )

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

    eliminar_separadores_internos(
        bloque
    )

    eliminar_separadores_finales(
        bloque
    )

    bloque.append(
        SEPARADOR
    )

    return bloque


# ============================================================
# HTML
# ============================================================

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
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
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
        json.dumps(
            video_url
        )
    )

    page = page.replace(
        "__URL_AUDIO_JS__",
        json.dumps(
            audio_url
        )
    )

    return page


# ============================================================
# ARGUMENTOS
# ============================================================

def build_parser():

    import argparse

    parser = argparse.ArgumentParser(

        description=(
            "Genera/actualiza index*.html "
            "y Lista_de_Enlaces_de_Videos.txt."
        ),

        epilog=(

            "Ejemplo:\n"

            '  ./generar_Index.py "Vinculo Sagrado"\n'

            '  ./generar_Index.py "Vinculo Sagrado" "portada.jpg"\n'

            '  ./generar_Index.py "Nueva Obra" "portada.jpg" "https://video" "https://audio"\n'

            '  ./generar_Index.py "Nueva Obra" "portada.jpg" "https://video" "https://audio" --info "Texto a probar"\n'

            '  ./generar_Index.py "Nueva Obra" "portada.jpg" --info "Solo información"'
        ),

        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "titulo",
        nargs="?",
        help="Título completo de la obra"
    )

    parser.add_argument(
        "imagen",
        nargs="?",
        help="portada.jpg, portada1.jpg, portada2.jpg, ..."
    )

    parser.add_argument(
        "url_video",
        nargs="?",
        help="URL video (opcional)"
    )

    parser.add_argument(
        "url_cancion",
        nargs="?",
        help="URL canción (opcional)"
    )

    parser.add_argument(
        "--info",
        default=None,
        help='Texto opcional para la clave info:'
    )

    parser.add_argument(
        "--db",
        default=DB_POR_DEFECTO,
        help="Archivo de base de datos"
    )

    return parser


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    parser = build_parser()

    args = parser.parse_args()

    if (
        not args.titulo
        or len(sys.argv) == 1
        or sys.argv[1] in ("-h", "--help")
    ):

        mostrar_ayuda()

    titulo = args.titulo.strip()

    restantes = sys.argv[2:]

    db_path = Path(
        args.db
    )

    if not db_path.is_absolute():

        db_path = (
            Path.cwd()
            / db_path
        )

    if not db_path.is_file():

        print(
            f"ERROR: No existe la base de datos: "
            f"{db_path}"
        )

        return 1

    # --------------------------------------------------------
    # LEER BASE
    # --------------------------------------------------------

    texto = db_path.read_text(
        encoding="utf-8"
    )

    entradas_raw = separar_entradas(
        texto
    )

    entradas = [
        analizar_entrada(bloque)
        for bloque in entradas_raw
    ]

    # --------------------------------------------------------
    # BUSCAR POR TÍTULO COMPLETO
    #
    # IMPORTANTE:
    # La búsqueda NO utiliza titulo_base_directorio().
    #
    # Esto permite tener:
    #
    # Personalidad_y_Esencia_(EPIC)
    # Personalidad_y_Esencia_(Personalitá e Essenza Italiano)
    #
    # como entradas independientes aunque compartan carpeta.
    # --------------------------------------------------------

    entrada = buscar_entrada(
        entradas,
        titulo
    )

    # --------------------------------------------------------
    # DIRECTORIO
    #
    # Todas las variantes pueden compartir el mismo directorio.
    # --------------------------------------------------------

    titulo1 = titulo_base_directorio(
        titulo
    )

    carpeta_titulo = (
        Path.cwd()
        / titulo1
    )

    # ========================================================
    # CASO 1:
    # TÍTULO EXISTENTE
    # ========================================================

    if entrada is not None:

        claves = entrada["claves"]

        # ----------------------------------------------------
        # IMAGEN
        # ----------------------------------------------------

        nombre_imagen = (
            restantes[0]
            if len(restantes) >= 1
            else None
        )

        if (
            not claves.get("url-imagen")
            and not nombre_imagen
        ):

            print(
                'ERROR: La entrada existe pero no tiene '
                '"url-imagen:" y no se indicó imagen.'
            )

            return 1

        if nombre_imagen:

            if not carpeta_titulo.is_dir():

                print(
                    f"ERROR: No existe la carpeta esperada: "
                    f"{carpeta_titulo}"
                )

                return 1

            imagen_path = (
                carpeta_titulo
                / nombre_imagen
            )

            if not imagen_path.is_file():

                print(
                    f"ERROR: No existe la imagen: "
                    f"{imagen_path}"
                )

                return 1

            imagen_usada = nombre_imagen

        else:

            imagen_usada = Path(
                claves["url-imagen"]
            ).name

        # ----------------------------------------------------
        # INDEX
        # ----------------------------------------------------

        html_name, web_name = (
            image_to_index_name(
                imagen_usada
            )
        )

        # ----------------------------------------------------
        # WEB VIDEO / WEB CANCION
        # ----------------------------------------------------

        web_video, web_cancion = (
            construir_web_urls(
                titulo,
                web_name
            )
        )

        # ----------------------------------------------------
        # URL VIDEO
        # ----------------------------------------------------

        url_video_param = (
            restantes[1]
            if len(restantes) >= 2
            else None
        )

        # ----------------------------------------------------
        # URL CANCION
        # ----------------------------------------------------

        url_cancion_param = (
            restantes[2]
            if len(restantes) >= 3
            else None
        )

        # ----------------------------------------------------
        # NORMALIZAR ENTRADA
        # ----------------------------------------------------

        nuevo_bloque = (
            normalizar_bloque_existente(

                entrada=entrada,

                titulo=titulo,

                nombre_imagen=nombre_imagen,

                url_video_param=url_video_param,

                url_cancion_param=url_cancion_param,

                info_param=args.info,

                web_video=web_video,

                web_cancion=web_cancion,
            )
        )

        # ----------------------------------------------------
        # REEMPLAZAR SOLO ESTA ENTRADA
        # ----------------------------------------------------

        reemplazo = (
            "\n".join(nuevo_bloque)
            + "\n"
        )

        texto_nuevo = texto.replace(
            entrada["bloque"],
            reemplazo,
            1
        )

        db_path.write_text(
            texto_nuevo,
            encoding="utf-8"
        )

        # ----------------------------------------------------
        # URL IMAGEN
        # ----------------------------------------------------

        url_imagen = construir_url_imagen(
            titulo,
            imagen_usada
        )

        # ----------------------------------------------------
        # URL VIDEO PARA HTML
        # ----------------------------------------------------

        url_video = (
            url_video_param
            if url_video_param is not None
            else claves.get(
                "url-video",
                ""
            )
        )

        if url_video is None:
            url_video = ""

        # ----------------------------------------------------
        # URL CANCION PARA HTML
        # ----------------------------------------------------

        url_cancion = (
            url_cancion_param
            if url_cancion_param is not None
            else claves.get(
                "url-cancion",
                ""
            )
        )

        if url_cancion is None:
            url_cancion = ""

        # ----------------------------------------------------
        # CREAR DIRECTORIO SI FUESE NECESARIO
        # ----------------------------------------------------

        carpeta_titulo.mkdir(
            parents=True,
            exist_ok=True
        )

        # ----------------------------------------------------
        # CREAR HTML
        # ----------------------------------------------------

        out_file = (
            carpeta_titulo
            / html_name
        )

        out_file.write_text(

            render_html(

                titulo,

                url_imagen,

                url_video,

                url_cancion,
            ),

            encoding="utf-8"
        )

        print()
        print(
            "Entrada existente actualizada correctamente."
        )
        print(
            f"Título   : {titulo}"
        )
        print(
            f"Directorio: {carpeta_titulo}"
        )
        print(
            f"Imagen   : {imagen_usada}"
        )
        print(
            f"HTML     : {out_file}"
        )
        print(
            f"WebVideo : {web_video}"
        )
        print(
            f"WebCanc. : {web_cancion}"
        )
        print()

        return 0

    # ========================================================
    # CASO 2:
    # TÍTULO NUEVO
    # ========================================================

    # Para una entrada nueva es obligatoria la imagen.

    if len(restantes) < 1:

        print()

        print(
            f'ERROR: El título "{titulo}" '
            f'no existe en la base de datos.'
        )

        print()

        print(
            "Para crear una nueva entrada necesitas:"
        )

        print(
            "  1) imagen"
        )

        print(
            "  2) url-video (opcional)"
        )

        print(
            "  3) url-cancion (opcional)"
        )

        print()

        print(
            "Ejemplo:"
        )

        print(
            f'  ./generar_Index.py '
            f'"{titulo}" "portada.jpg"'
        )

        print()

        return 1

    # --------------------------------------------------------
    # PARÁMETROS
    # --------------------------------------------------------

    nombre_imagen = restantes[0]

    url_video_param = (
        restantes[1]
        if len(restantes) >= 2
        else ""
    )

    url_cancion_param = (
        restantes[2]
        if len(restantes) >= 3
        else ""
    )

    # --------------------------------------------------------
    # DIRECTORIO
    # --------------------------------------------------------

    if not carpeta_titulo.is_dir():

        print(
            f"ERROR: No existe la carpeta del título: "
            f"{carpeta_titulo}"
        )

        return 1

    # --------------------------------------------------------
    # IMAGEN
    # --------------------------------------------------------

    imagen_path = (
        carpeta_titulo
        / nombre_imagen
    )

    if not imagen_path.is_file():

        print(
            f"ERROR: No existe la imagen: "
            f"{imagen_path}"
        )

        return 1

    # --------------------------------------------------------
    # NÚMERO
    # --------------------------------------------------------

    numero_nuevo = siguiente_indice(
        entradas
    )

    # --------------------------------------------------------
    # INDEX
    # --------------------------------------------------------

    html_name, web_name = (
        image_to_index_name(
            nombre_imagen
        )
    )

    # --------------------------------------------------------
    # WEB URLS
    # --------------------------------------------------------

    web_video, web_cancion = (
        construir_web_urls(
            titulo,
            web_name
        )
    )

    # --------------------------------------------------------
    # INFO
    # --------------------------------------------------------

    info_nueva = (
        args.info
        if args.info is not None
        else "N.A."
    )

    # --------------------------------------------------------
    # CREAR BLOQUE
    # --------------------------------------------------------

    nuevo_bloque = crear_bloque_nuevo(

        numero=numero_nuevo,

        titulo=titulo,

        nombre_imagen=nombre_imagen,

        url_video=url_video_param,

        url_cancion=url_cancion_param,

        info=info_nueva,

        web_video=web_video,

        web_cancion=web_cancion,
    )

    # --------------------------------------------------------
    # AGREGAR A LA BASE
    #
    # Se garantiza:
    #
    # ...SEPARADOR\n
    #
    # y NO:
    #
    # ...SEPARADOR
    # --------------------------------------------------------

    texto = (
        texto.rstrip("\n")
        + "\n"
        + "\n".join(nuevo_bloque)
        + "\n"
    )

    db_path.write_text(
        texto,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # URL IMAGEN
    # --------------------------------------------------------

    url_imagen = construir_url_imagen(
        titulo,
        nombre_imagen
    )

    # --------------------------------------------------------
    # DIRECTORIO
    # --------------------------------------------------------

    carpeta_titulo.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    out_file = (
        carpeta_titulo
        / html_name
    )

    out_file.write_text(

        render_html(

            titulo,

            url_imagen,

            url_video_param,

            url_cancion_param,
        ),

        encoding="utf-8"
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print()

    print(
        "Nueva entrada creada correctamente."
    )

    print(
        f"Indice   : {numero_nuevo}"
    )

    print(
        f"Título   : {titulo}"
    )

    print(
        f"Directorio: {carpeta_titulo}"
    )

    print(
        f"Imagen   : {nombre_imagen}"
    )

    print(
        f"HTML     : {out_file}"
    )

    print(
        f"WebVideo : {web_video}"
    )

    print(
        f"WebCanc. : {web_cancion}"
    )

    print()

    return 0


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    raise SystemExit(
        main()
    )

"""
================================================================================
Módulo de Adquisición y Análisis de Imágenes - FPDI 2026
Fundamentos del Procesamiento Digital de Imágenes
================================================================================

Este módulo proporciona funciones reutilizables para:
1. Cargar y capturar imágenes (`cargar_imagen`, `capturar_webcam`).
2. Diagnóstico técnico, matricial, memoria y compresión (`info_imagen`).
3. Extracción robusta de metadatos fotográficos y geolocalización (`leer_exif`).
4. Visualización interactiva y descomposición espectral (`mostrar_imagen`, `mostrar_canales`).

Diseñado para ser importado como librería base en los Trabajos Prácticos (TPs) de la cursada:
    from adquisicion import cargar_imagen, info_imagen, leer_exif, capturar_webcam, mostrar_imagen
"""

import os
import sys
import time
from typing import Optional, Dict, Any, Tuple, Union
import cv2
import numpy as np
from PIL import Image, ExifTags

# Configuración de codificación UTF-8 en consola para Windows
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ==============================================================================
# 1. FUNCIONES DE ADQUISICIÓN Y CARGA DE IMÁGENES
# ==============================================================================

def cargar_imagen(
    origen: Optional[str] = None,
    modo: str = "BGR",
    abrir_dialogo: bool = False,
    retornar_ruta: bool = False
) -> Union[Optional[np.ndarray], Tuple[Optional[np.ndarray], Optional[str]]]:
    """
    Carga una imagen digital desde un archivo en disco o mediante un diálogo interactivo.

    Parámetros:
        origen (str, opcional): Ruta al archivo de imagen en disco (ej. 'foto.jpg').
                                Si es None y abrir_dialogo=True, abre el explorador gráfico.
        modo (str): Espacio de color objetivo en el que se retorna el arreglo NumPy.
                    Opciones:
                    - 'BGR': Formato nativo de OpenCV (Azul, Verde, Rojo). [Por defecto]
                    - 'RGB': Formato estándar (Rojo, Verde, Azul), ideal para Matplotlib/Pillow.
                    - 'GRAY' o 'GRIS': Monocromático de 1 solo canal (escala de grises).
                    - 'UNCHANGED': Conserva el formato original del archivo (incluyendo canal Alpha RGBA si existe).
        abrir_dialogo (bool): Si es True y origen es None, abre el diálogo gráfico del SO para elegir el archivo.
        retornar_ruta (bool): Si es True, retorna una tupla (imagen, ruta_archivo). Si es False, retorna solo la imagen.

    Retorna:
        np.ndarray o (np.ndarray, str): Arreglo NumPy con la imagen cargada o None si falló/se canceló.

    Ejemplo de uso:
        >>> # Carga básica en BGR para OpenCV:
        >>> img = cargar_imagen("muestras/foto.jpg")
        >>> # Carga convertida directamente a RGB para graficar con Matplotlib:
        >>> img_rgb = cargar_imagen("muestras/foto.jpg", modo="RGB")
        >>> # Carga interactiva mediante ventana gráfica:
        >>> img, ruta = cargar_imagen(abrir_dialogo=True, retornar_ruta=True)
    """
    ruta_final = origen

    if ruta_final is None and abrir_dialogo:
        ruta_final = _abrir_dialogo_archivo()
        if not ruta_final:
            print("[INFO] Selección de archivo cancelada.")
            return (None, None) if retornar_ruta else None

    if not ruta_final or not os.path.exists(ruta_final):
        print(f"[ERROR] La ruta especificada no existe: '{ruta_final}'")
        return (None, None) if retornar_ruta else None

    # Lectura binaria segura compatible con rutas con caracteres especiales/espacios en Windows
    try:
        with open(ruta_final, "rb") as f:
            datos_bytes = bytearray(f.read())
            arr_np = np.asarray(datos_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr_np, cv2.IMREAD_UNCHANGED)

        if img is None:
            print(f"[ERROR] No se pudo decodificar la imagen desde: '{ruta_final}'")
            return (None, None) if retornar_ruta else None

        # Conversiones de espacio de color solicitadas
        modo_upper = modo.upper()
        if modo_upper in ["GRAY", "GRIS"]:
            if len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elif modo_upper == "RGB":
            if len(img.shape) == 3:
                if img.shape[2] == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                elif img.shape[2] == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
            elif len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        elif modo_upper == "BGR":
            if len(img.shape) == 3 and img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            elif len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        # Si es 'UNCHANGED', se deja tal como viene decodificada

        return (img, ruta_final) if retornar_ruta else img

    except Exception as e:
        print(f"[ERROR] Excepción al cargar imagen: {str(e)}")
        return (None, None) if retornar_ruta else None


def capturar_webcam(
    camera_index: int = 0,
    guardar_ruta: Optional[str] = None,
    modo: str = "BGR"
) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Captura un fotograma en vivo desde la cámara web o dispositivo de captura usando OpenCV.
    Abre una ventana de previsualización en tiempo real.

    Controles en la ventana de previsualización:
        - ESPACIO o ENTER: Congela y captura el fotograma actual.
        - ESC o 'Q': Cancela la captura y cierra la ventana.

    Parámetros:
        camera_index (int): Índice del dispositivo de video (0 = cámara predeterminada).
        guardar_ruta (str, opcional): Ruta donde guardar el fotograma en disco (ej. 'captura.jpg').
                                      Si es None, genera automáticamente un archivo con marca de tiempo en 'capturas/'.
        modo (str): 'BGR', 'RGB' o 'GRAY'.

    Retorna:
        Tuple[np.ndarray, str]: (imagen_capturada, ruta_guardada_en_disco). Ambos None si se canceló.

    Ejemplo de uso:
        >>> img, path = capturar_webcam()
        >>> if img is not None:
        >>>     print(f"Imagen capturada con shape {img.shape} guardada en {path}")
    """
    print(f"\n[INFO] Inicializando cámara web (Dispositivo {camera_index})...")

    if sys.platform.startswith("win"):
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(camera_index)
    else:
        cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"[ERROR] No se pudo abrir la cámara {camera_index}. Verifique permisos o conexión.")
        return None, None

    window_title = "FPDI 2026 - Captura en Vivo (ESPACIO/ENTER: Capturar | ESC/Q: Cancelar)"
    cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)

    frame_capturado = None
    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[WARN] Fotograma no disponible.")
                break

            # Superposición visual informativa para el usuario
            display_preview = frame.copy()
            h, w = display_preview.shape[:2]
            cv2.rectangle(display_preview, (0, 0), (w, 36), (20, 20, 20), -1)
            cv2.putText(
                display_preview,
                "ESPACIO / ENTER: Capturar  |  ESC / Q: Cancelar",
                (12, 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
                cv2.LINE_AA
            )

            cv2.imshow(window_title, display_preview)
            key = cv2.waitKey(20) & 0xFF

            if key in [32, 13]:  # Espacio o Enter
                frame_capturado = frame.copy()
                print("[OK] ¡Fotograma capturado con éxito!")
                break
            elif key in [27, ord('q'), ord('Q')]:  # ESC o Q
                print("[INFO] Captura cancelada.")
                break
    finally:
        cap.release()
        cv2.destroyWindow(window_title)

    if frame_capturado is None:
        return None, None

    # Guardar en disco
    if guardar_ruta is None:
        os.makedirs("capturas", exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        guardar_ruta = os.path.join("capturas", f"captura_webcam_{ts}.jpg")

    cv2.imwrite(guardar_ruta, frame_capturado)
    print(f"[OK] Fotograma guardado en: '{guardar_ruta}'")

    # Conversión de color si fue requerida
    if modo.upper() == "RGB":
        frame_capturado = cv2.cvtColor(frame_capturado, cv2.COLOR_BGR2RGB)
    elif modo.upper() in ["GRAY", "GRIS"]:
        frame_capturado = cv2.cvtColor(frame_capturado, cv2.COLOR_BGR2GRAY)

    return frame_capturado, guardar_ruta


# ==============================================================================
# 2. DIAGNÓSTICO TÉCNICO, MEMORIA, COMPRESIÓN Y COLOR
# ==============================================================================

def info_imagen(
    imagen: np.ndarray,
    ruta_archivo: Optional[str] = None,
    orden_color: str = "BGR",
    imprimir_reporte: bool = True
) -> Dict[str, Any]:
    """
    Analiza exhaustivamente las propiedades numéricas, estructurales y de almacenamiento de una imagen.

    Reporta:
        - Dimensiones espaciales (Alto, Ancho, Canales, Megapíxeles).
        - Tipo de dato NumPy (dtype), bytes por muestra y profundidad en bits por canal y por píxel.
        - Tamaño exacto en memoria RAM (matriz cruda continua) vs. tamaño del archivo comprimido en disco.
        - Factor de compresión (RAM:Disco) y porcentaje de reducción de espacio.
        - Explicación de las discrepancias de tamaño (compresión JPEG con pérdida DCT / PNG sin pérdida DEFLATE).
        - Espacio y orden de canales de color (BGR vs. RGB) con advertencia didáctica de OpenCV.

    Parámetros:
        imagen (np.ndarray): Matriz NumPy que representa la imagen.
        ruta_archivo (str, opcional): Ruta al archivo en disco (si existe) para calcular compresión.
        orden_color (str): 'BGR', 'RGB', 'GRAY' o 'BGRA'.
        imprimir_reporte (bool): Si es True, imprime un reporte formateado y legible en consola.

    Retorna:
        Dict[str, Any]: Diccionario con todos los datos numéricos y conceptuales del análisis.

    Ejemplo de uso:
        >>> datos = info_imagen(img, "foto.jpg")
        >>> print("Total píxeles:", datos["total_pixeles"])
        >>> print("RAM:", datos["ram_formateado"], "vs Disco:", datos["disco_formateado"])
    """
    if not isinstance(imagen, np.ndarray):
        raise TypeError("El parámetro 'imagen' debe ser un arreglo de tipo numpy.ndarray.")

    # 1. Dimensiones y canales
    shape = imagen.shape
    if len(shape) == 2:
        alto, ancho = shape
        canales = 1
    elif len(shape) == 3:
        alto, ancho, canales = shape
    else:
        alto, ancho, canales = shape[0], shape[1], shape[2] if len(shape) > 2 else 1

    total_pixeles = int(alto * ancho)
    megapixeles = total_pixeles / 1_000_000.0

    # 2. Profundidad de bits y tipo de dato
    dtype_str = str(imagen.dtype)
    itemsize_bytes = int(imagen.itemsize)
    bits_por_canal = itemsize_bytes * 8
    bits_por_pixel = bits_por_canal * canales

    # 3. Tamaño en memoria RAM
    ram_bytes = int(imagen.nbytes)
    ram_formateado = _formatear_bytes(ram_bytes)

    # 4. Tamaño en disco y compresión
    disco_bytes = None
    disco_formateado = "N/A (En memoria)"
    ratio_compresion = None
    porcentaje_ahorro = None

    if ruta_archivo and os.path.exists(ruta_archivo):
        disco_bytes = int(os.path.getsize(ruta_archivo))
        disco_formateado = _formatear_bytes(disco_bytes)
        if disco_bytes > 0:
            ratio_compresion = float(ram_bytes / disco_bytes)
            porcentaje_ahorro = float((1.0 - (disco_bytes / ram_bytes)) * 100.0)

    # 5. Explicación teórica de compresión
    explicacion_compresion = _generar_explicacion_compresion(
        ram_bytes=ram_bytes,
        disco_bytes=disco_bytes,
        ruta_archivo=ruta_archivo
    )

    # 6. Espacio de color
    espacio_color, explicacion_color = _analizar_espacio_color(canales, orden_color)

    resultado = {
        "alto": alto,
        "ancho": ancho,
        "canales": canales,
        "shape": shape,
        "total_pixeles": total_pixeles,
        "megapixeles": megapixeles,
        "dtype": dtype_str,
        "itemsize_bytes": itemsize_bytes,
        "bits_por_canal": bits_por_canal,
        "bits_por_pixel": bits_por_pixel,
        "ram_bytes": ram_bytes,
        "ram_formateado": ram_formateado,
        "disco_bytes": disco_bytes,
        "disco_formateado": disco_formateado,
        "ratio_compresion": ratio_compresion,
        "porcentaje_ahorro": porcentaje_ahorro,
        "espacio_color": espacio_color,
        "explicacion_color": explicacion_color,
        "explicacion_compresion": explicacion_compresion,
        "ruta_archivo": ruta_archivo
    }

    if imprimir_reporte:
        _imprimir_reporte_tecnico(resultado)

    return resultado


# ==============================================================================
# 3. EXTRACCIÓN Y DIAGNÓSTICO DE METADATOS EXIF Y GPS
# ==============================================================================

def leer_exif(
    ruta_archivo: Optional[str],
    imprimir_reporte: bool = False
) -> Dict[str, Any]:
    """
    Extrae de forma segura y estructurada los metadatos EXIF fotográficos y geográficos.
    
    Diseñado con tolerancia a fallos: Si la imagen no contiene EXIF (capturas de pantalla,
    WhatsApp, redes sociales o fotogramas de webcam), informa con precisión la causa en
    lugar de generar excepciones o errores en tiempo de ejecución.

    Parámetros:
        ruta_archivo (str, opcional): Ruta al archivo de imagen en disco.
        imprimir_reporte (bool): Si es True, muestra el informe formateado en consola.

    Retorna:
        Dict[str, Any] con las siguientes claves:
            - 'tiene_exif' (bool): True si se encontraron metadatos válidos.
            - 'mensaje' (str): Diagnóstico o estado de la lectura.
            - 'fabricante' (str): Make de la cámara.
            - 'modelo' (str): Modelo de la cámara / smartphone.
            - 'software' (str): Firmware o programa de procesado.
            - 'fecha_hora' (str): Fecha y hora de captura original.
            - 'iso' (int): Sensibilidad ISO del sensor.
            - 'apertura_f' (str): Número f de apertura del diafragma (ej. 'f/2.8').
            - 'tiempo_exposicion' (str): Velocidad de obturación (ej. '1/500 s').
            - 'distancia_focal' (str): Distancia focal en mm (ej. '50.0 mm').
            - 'distancia_focal_35mm' (str): Equivalente en formato full-frame 35mm.
            - 'balance_blancos' (str): Modo de balance de blancos ('Automático' / 'Manual').
            - 'modo_medicion' (str): Medición fotométrica ('Matricial', 'Puntual', etc.).
            - 'lente' (str): Modelo del lente u objetivo óptico.
            - 'gps' (dict, opcional): {'latitud_decimal', 'longitud_decimal', 'altitud_m',
                                       'latitud_dms', 'longitud_dms', 'google_maps_url'}
            - 'tags_crudos' (dict): Diccionario con todas las etiquetas decodificadas.

    Ejemplo de uso:
        >>> exif_data = leer_exif("foto_camara.jpg", imprimir_reporte=True)
        >>> if exif_data["tiene_exif"]:
        >>>     print(f"Cámara: {exif_data['fabricante']} {exif_data['modelo']}")
        >>>     print(f"Exposición: ISO {exif_data['iso']} - {exif_data['apertura_f']} - {exif_data['tiempo_exposicion']}")
        >>>     if exif_data["gps"]:
        >>>         print(f"Ubicación: {exif_data['gps']['google_maps_url']}")
    """
    if not ruta_archivo:
        res_vacio = {
            "tiene_exif": False,
            "mensaje": (
                "No se especificó un archivo en disco (imagen adquirida directamente en memoria RAM desde webcam).\n"
                "Los fotogramas en vivo capturados por OpenCV VideoCapture no poseen contenedor de metadatos EXIF."
            ),
            "fabricante": None,
            "modelo": None,
            "software": None,
            "fecha_hora": None,
            "iso": None,
            "apertura_f": None,
            "tiempo_exposicion": None,
            "distancia_focal": None,
            "distancia_focal_35mm": None,
            "balance_blancos": None,
            "modo_medicion": None,
            "lente": None,
            "gps": None,
            "tags_crudos": {}
        }
        if imprimir_reporte:
            _imprimir_reporte_exif(res_vacio)
        return res_vacio

    if not os.path.exists(ruta_archivo):
        res_error = {
            "tiene_exif": False,
            "mensaje": f"El archivo no existe: '{ruta_archivo}'",
            "fabricante": None,
            "modelo": None,
            "software": None,
            "fecha_hora": None,
            "iso": None,
            "apertura_f": None,
            "tiempo_exposicion": None,
            "distancia_focal": None,
            "distancia_focal_35mm": None,
            "balance_blancos": None,
            "modo_medicion": None,
            "lente": None,
            "gps": None,
            "tags_crudos": {}
        }
        if imprimir_reporte:
            _imprimir_reporte_exif(res_error)
        return res_error

    try:
        with Image.open(ruta_archivo) as pil_img:
            raw_exif = pil_img.getexif()

            if not raw_exif:
                return _crear_reporte_exif_vacio(ruta_archivo, imprimir_reporte)

            decoded_tags: Dict[str, Any] = {}
            # IFD0 principal
            for tag_id, val in raw_exif.items():
                decoded_tags[ExifTags.TAGS.get(tag_id, str(tag_id))] = val

            # Sub-IFD Exif
            try:
                exif_ifd = raw_exif.get_ifd(ExifTags.IFD.Exif)
                for tag_id, val in exif_ifd.items():
                    decoded_tags[ExifTags.TAGS.get(tag_id, str(tag_id))] = val
            except Exception:
                pass

            # Sub-IFD GPS
            gps_raw: Dict[str, Any] = {}
            try:
                gps_ifd = raw_exif.get_ifd(ExifTags.IFD.GPSInfo)
                for tag_id, val in gps_ifd.items():
                    gps_raw[ExifTags.GPSTAGS.get(tag_id, str(tag_id))] = val
            except Exception:
                pass

            if not decoded_tags and not gps_raw:
                return _crear_reporte_exif_vacio(ruta_archivo, imprimir_reporte)

            # Campos individuales
            fabricante = str(decoded_tags.get("Make", "")).strip() or None
            modelo = str(decoded_tags.get("Model", "")).strip() or None
            software = str(decoded_tags.get("Software", "")).strip() or None
            fecha_hora = str(decoded_tags.get("DateTimeOriginal") or decoded_tags.get("DateTime") or "").strip() or None

            # ISO
            iso_val = decoded_tags.get("ISOSpeedRatings") or decoded_tags.get("PhotographicSensitivity")
            iso = int(iso_val) if iso_val is not None else None

            # Apertura
            fnumber = _formatear_fnumber(decoded_tags.get("FNumber"))

            # Tiempo de exposición
            exp_time = _formatear_tiempo_exposicion(decoded_tags.get("ExposureTime"))

            # Distancia focal
            focal = _formatear_focal(decoded_tags.get("FocalLength"))
            focal_35mm_val = decoded_tags.get("FocalLengthIn35mmFilm")
            focal_35mm = f"{focal_35mm_val} mm (equiv. 35mm)" if focal_35mm_val else None

            # Balance de blancos
            wb_val = decoded_tags.get("WhiteBalance")
            wb = "Manual" if wb_val == 1 else ("Automático" if wb_val == 0 else (str(wb_val) if wb_val is not None else None))

            # Modo de medición
            metering = _formatear_modo_medicion(decoded_tags.get("MeteringMode"))
            lente = str(decoded_tags.get("LensModel", "")).strip() or None

            # GPS
            gps_info = _parsear_gps(gps_raw)

            reporte = {
                "tiene_exif": True,
                "mensaje": "Metadatos EXIF extraídos exitosamente.",
                "fabricante": fabricante,
                "modelo": modelo,
                "software": software,
                "fecha_hora": fecha_hora,
                "iso": iso,
                "apertura_f": fnumber,
                "tiempo_exposicion": exp_time,
                "distancia_focal": focal,
                "distancia_focal_35mm": focal_35mm,
                "balance_blancos": wb,
                "modo_medicion": metering,
                "lente": lente,
                "gps": gps_info,
                "tags_crudos": decoded_tags
            }

            if imprimir_reporte:
                _imprimir_reporte_exif(reporte)

            return reporte

    except Exception as e:
        reporte_err = {
            "tiene_exif": False,
            "mensaje": f"No fue posible leer metadatos EXIF ({str(e)}).",
            "fabricante": None,
            "modelo": None,
            "software": None,
            "fecha_hora": None,
            "iso": None,
            "apertura_f": None,
            "tiempo_exposicion": None,
            "distancia_focal": None,
            "distancia_focal_35mm": None,
            "balance_blancos": None,
            "modo_medicion": None,
            "lente": None,
            "gps": None,
            "tags_crudos": {}
        }
        if imprimir_reporte:
            _imprimir_reporte_exif(reporte_err)
        return reporte_err


# ==============================================================================
# 4. VISUALIZACIÓN INTERACTIVA Y DESCOMPOSICIÓN DE CANALES
# ==============================================================================

def mostrar_imagen(
    imagen: np.ndarray,
    titulo: str = "FPDI 2026 - Visualizador",
    orden_color: str = "BGR",
    esperar_tecla: bool = True
) -> None:
    """
    Muestra una imagen en una ventana de OpenCV.
    
    Parámetros:
        imagen (np.ndarray): Imagen a mostrar.
        titulo (str): Título de la ventana.
        orden_color (str): 'BGR', 'RGB' o 'GRAY'. Si es 'RGB', la convierte a 'BGR' para que OpenCV la pinte bien.
        esperar_tecla (bool): Si es True, pausa la ejecución hasta que el usuario presione una tecla en la ventana.
    """
    if not isinstance(imagen, np.ndarray):
        print("[ERROR] 'imagen' debe ser un arreglo NumPy.")
        return

    img_mostrar = imagen.copy()
    if orden_color.upper() == "RGB" and len(img_mostrar.shape) == 3:
        img_mostrar = cv2.cvtColor(img_mostrar, cv2.COLOR_RGB2BGR)

    cv2.namedWindow(titulo, cv2.WINDOW_NORMAL)
    cv2.imshow(titulo, img_mostrar)
    if esperar_tecla:
        print(f"[INFO] Mostrando '{titulo}'. Presione cualquier tecla en la ventana para cerrarla.")
        cv2.waitKey(0)
        cv2.destroyWindow(titulo)


def mostrar_canales(
    imagen: np.ndarray,
    orden_color: str = "BGR",
    titulo: str = "FPDI 2026 - Descomposición de Canales (Original | B | G | R)"
) -> None:
    """
    Genera y muestra una matriz didáctica 2x2 con la descomposición de los 3 canales fundamentales:
    [ Imagen Original ] [ Canal Azul (B) ]
    [ Canal Verde (G) ] [ Canal Rojo (R) ]
    """
    if len(imagen.shape) == 2:
        print("[INFO] Imagen monocromática (1 solo canal de luminancia).")
        mostrar_imagen(imagen, titulo="FPDI 2026 - Imagen Monocromática")
        return

    if len(imagen.shape) != 3 or imagen.shape[2] < 3:
        mostrar_imagen(imagen, titulo=titulo)
        return

    bgr = imagen[:, :, :3] if orden_color.upper() == "BGR" else cv2.cvtColor(imagen[:, :, :3], cv2.COLOR_RGB2BGR)
    b, g, r = cv2.split(bgr)
    ceros = np.zeros_like(b)

    # Canales coloreados individualmente
    azul = cv2.merge([b, ceros, ceros])
    verde = cv2.merge([ceros, g, ceros])
    rojo = cv2.merge([ceros, ceros, r])

    def rotular(cuad, texto):
        c = cuad.copy()
        cv2.rectangle(c, (0, 0), (len(texto) * 15 + 15, 30), (0, 0, 0), -1)
        cv2.putText(c, texto, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        return c

    q1 = rotular(bgr, "Original (BGR)")
    q2 = rotular(azul, "Canal B (Azul)")
    q3 = rotular(verde, "Canal G (Verde)")
    q4 = rotular(rojo, "Canal R (Rojo)")

    # Escalar proporcionalmente si excede tamaño de pantalla
    max_d = 400
    h, w = bgr.shape[:2]
    escala = min(max_d / max(h, 1), max_d / max(w, 1), 1.0)
    if escala < 1.0:
        nw, nh = int(w * escala), int(h * escala)
        q1 = cv2.resize(q1, (nw, nh))
        q2 = cv2.resize(q2, (nw, nh))
        q3 = cv2.resize(q3, (nw, nh))
        q4 = cv2.resize(q4, (nw, nh))

    mosaico = np.vstack([np.hstack([q1, q2]), np.hstack([q3, q4])])
    cv2.namedWindow(titulo, cv2.WINDOW_AUTOSIZE)
    cv2.imshow(titulo, mosaico)
    print(f"[INFO] Mostrando cuadrante de canales. Presione una tecla en la ventana para continuar.")
    cv2.waitKey(0)
    cv2.destroyWindow(titulo)


# ==============================================================================
# FUNCIONES AUXILIARES INTERNAS
# ==============================================================================

def _abrir_dialogo_archivo() -> Optional[str]:
    """Abre un diálogo gráfico para seleccionar archivo."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askopenfilename(
            title="Seleccionar Imagen - FPDI 2026",
            filetypes=[
                ("Archivos de Imagen", "*.jpg *.jpeg *.png *.bmp *.webp *.tiff *.tif *.dng *.raw"),
                ("Todos los archivos", "*.*")
            ]
        )
        root.destroy()
        return path if path else None
    except Exception:
        return None


def _formatear_bytes(b: int) -> str:
    """Convierte bytes a formato KB, MB o GB con separadores."""
    if b < 1024:
        return f"{b} Bytes"
    elif b < 1024 * 1024:
        return f"{b / 1024:.2f} KB ({b:,} Bytes)"
    elif b < 1024 * 1024 * 1024:
        return f"{b / (1024 * 1024):.2f} MB ({b:,} Bytes)"
    else:
        return f"{b / (1024 * 1024 * 1024):.2f} GB ({b:,} Bytes)"


def _generar_explicacion_compresion(ram_bytes: int, disco_bytes: Optional[int], ruta_archivo: Optional[str]) -> str:
    """Genera la fundamentación teórica de la discrepancia de memoria RAM vs Disco."""
    if disco_bytes is None:
        return (
            "Imagen generada o capturada directamente en memoria RAM (ej. Webcam).\n"
            f"- Tamaño en memoria RAM: {_formatear_bytes(ram_bytes)}.\n"
            "- No posee archivo asociado en disco actualmente. Al exportarla (ej. en .jpg o .png), "
            "se aplicarán algoritmos de compresión que reducirán sustancialmente el tamaño de almacenamiento."
        )

    ext = os.path.splitext(ruta_archivo)[1].lower() if ruta_archivo else ""
    ratio = ram_bytes / disco_bytes if disco_bytes > 0 else 1.0

    lineas = [
        f"• Tamaño en RAM (Matriz cruda descomprimida): {_formatear_bytes(ram_bytes)}",
        f"• Tamaño en Disco (Archivo codificado/comprimido): {_formatear_bytes(disco_bytes)}",
        f"• Factor de compresión: {ratio:.2f}:1 ({((1 - disco_bytes / ram_bytes) * 100):.1f}% de ahorro en disco)."
    ]

    if ext in ['.jpg', '.jpeg']:
        lineas.append(
            "\nFundamento Teórico (Compresión con pérdida - JPEG):\n"
            "1. En memoria RAM, la imagen reside como un tensor NumPy continuo de valores numéricos directos "
            "(alto × ancho × canales), permitiendo acceso aleatorio inmediato O(1) a cada píxel.\n"
            "2. En disco (.jpg), JPEG aplica Transformada Discreta del Coseno (DCT) en bloques de 8x8, cuantiza y "
            "descarta altas frecuencias espaciales menos sensibles al ojo humano, aplica submuestreo de croma (YCbCr) "
            "y codificación de entropía (Huffman/RLE)."
        )
    elif ext in ['.png']:
        lineas.append(
            "\nFundamento Teórico (Compresión sin pérdida - PNG):\n"
            "1. En memoria RAM, los canales se encuentran completamente expandidos.\n"
            "2. En disco (.png), PNG aplica filtros de predicción espacial (Sub, Up, Average, Paeth) combinados "
            "con el algoritmo DEFLATE (LZ77 + Huffman) para comprimir sin perder un solo valor numérico de la matriz original."
        )
    elif ext in ['.bmp', '.raw', '.dng']:
        lineas.append(
            "\nFundamento Teórico (Formato crudo / sin compresión):\n"
            "El formato almacena directamente los píxeles rasterizados con una cabecera básica, "
            "por lo que el tamaño en disco es prácticamente idéntico al tamaño en RAM."
        )
    else:
        lineas.append(
            "\nFundamento Teórico:\n"
            "La memoria RAM mantiene los valores numéricos crudos para procesamiento algebraico matricial, "
            "mientras que el archivo en disco está optimizado mediante algoritmos de codificación."
        )

    return "\n".join(lineas)


def _analizar_espacio_color(canales: int, orden_color: str) -> Tuple[str, str]:
    """Analiza el espacio y el orden de canales de color."""
    if canales == 1:
        return (
            "Escala de Grises (Monocromático / Intensidad Y)",
            "Posee 1 solo canal de luminancia por píxel (valores típicamente en rango [0, 255])."
        )
    elif canales == 3:
        if orden_color.upper() == "BGR":
            return (
                "BGR (Blue, Green, Red - Orden nativo OpenCV)",
                "¡Cuidado con OpenCV!\n"
                "- OpenCV decodifica y representa imágenes por defecto en orden BGR (Azul, Verde, Rojo).\n"
                "- Proviene de convenciones históricas de hardware y del formato BMP/DIB de Windows.\n"
                "- Librerías como Matplotlib, Pillow y los navegadores web esperan orden RGB.\n"
                "- Conversión: cv2.cvtColor(img, cv2.COLOR_BGR2RGB)."
            )
        else:
            return (
                "RGB (Red, Green, Blue - Estándar Matplotlib / Pillow)",
                "Estructurada en orden estándar RGB: Canal 0 = Rojo, Canal 1 = Verde, Canal 2 = Azul."
            )
    elif canales == 4:
        return (
            "BGRA / RGBA (Color con canal Alpha)",
            "Posee 4 canales: los 3 de color más el canal Alpha (A) que codifica la opacidad o transparencia."
        )
    else:
        return (f"Multiespectral ({canales} canales)", f"Matriz con {canales} bandas espectrales.")


def _crear_reporte_exif_vacio(ruta: str, imprimir: bool) -> Dict[str, Any]:
    """Genera el reporte cuando no existen metadatos EXIF en la imagen."""
    msg = (
        "⚠️ No se detectaron metadatos EXIF en esta imagen.\n\n"
        "Causas habituales en Procesamiento Digital de Imágenes:\n"
        "1. Mensajería / Redes Sociales (WhatsApp, Telegram, Instagram): eliminan metadatos por privacidad y compresión.\n"
        "2. Capturas de pantalla o imágenes sintéticas: no se capturan con un sensor óptico con diafragma/obturador.\n"
        "3. Editores de imágenes: al exportar en PNG o formatos simples se descartan los bloques de metadatos."
    )
    res = {
        "tiene_exif": False,
        "mensaje": msg,
        "fabricante": None,
        "modelo": None,
        "software": None,
        "fecha_hora": None,
        "iso": None,
        "apertura_f": None,
        "tiempo_exposicion": None,
        "distancia_focal": None,
        "distancia_focal_35mm": None,
        "balance_blancos": None,
        "modo_medicion": None,
        "lente": None,
        "gps": None,
        "tags_crudos": {}
    }
    if imprimir:
        _imprimir_reporte_exif(res)
    return res


def _formatear_fnumber(val: Any) -> Optional[str]:
    if val is None:
        return None
    try:
        f = float(val)
        return f"f/{f:.1f}" if f % 1 != 0 else f"f/{int(f)}"
    except Exception:
        return str(val)


def _formatear_tiempo_exposicion(val: Any) -> Optional[str]:
    if val is None:
        return None
    try:
        t = float(val)
        if t <= 0:
            return str(val)
        if t < 1.0:
            inv = round(1.0 / t)
            return f"1/{inv} s ({t:.5f} s)"
        else:
            return f"{t:.2f} s"
    except Exception:
        return str(val)


def _formatear_focal(val: Any) -> Optional[str]:
    if val is None:
        return None
    try:
        fl = float(val)
        return f"{fl:.1f} mm" if fl % 1 != 0 else f"{int(fl)} mm"
    except Exception:
        return f"{val} mm"


def _formatear_modo_medicion(val: Any) -> Optional[str]:
    modos = {
        0: "Desconocido", 1: "Promedio", 2: "Ponderado al centro",
        3: "Puntual (Spot)", 4: "Multi-punto", 5: "Matricial (Multi-segmento)",
        6: "Parcial", 255: "Otro"
    }
    return modos.get(val, str(val) if val is not None else None)


def _dms_a_decimal(dms: Tuple[Any, Any, Any], ref: str) -> float:
    deg = float(dms[0])
    minu = float(dms[1])
    sec = float(dms[2])
    dec = deg + (minu / 60.0) + (sec / 3600.0)
    if ref.upper() in ['S', 'W']:
        dec = -dec
    return dec


def _parsear_gps(gps_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not gps_dict:
        return None
    try:
        lat_dms = gps_dict.get("GPSLatitude")
        lat_ref = gps_dict.get("GPSLatitudeRef", "N")
        lon_dms = gps_dict.get("GPSLongitude")
        lon_ref = gps_dict.get("GPSLongitudeRef", "E")

        if not lat_dms or not lon_dms:
            return None

        lat_dec = _dms_a_decimal(lat_dms, lat_ref)
        lon_dec = _dms_a_decimal(lon_dms, lon_ref)

        alt_val = gps_dict.get("GPSAltitude")
        alt_m = float(alt_val) if alt_val is not None else None

        lat_str = f"{float(lat_dms[0]):.0f}° {float(lat_dms[1]):.0f}' {float(lat_dms[2]):.2f}'' {lat_ref}"
        lon_str = f"{float(lon_dms[0]):.0f}° {float(lon_dms[1]):.0f}' {float(lon_dms[2]):.2f}'' {lon_ref}"
        maps_url = f"https://www.google.com/maps?q={lat_dec:.6f},{lon_dec:.6f}"

        return {
            "latitud_decimal": lat_dec,
            "longitud_decimal": lon_dec,
            "altitud_m": alt_m,
            "latitud_dms": lat_str,
            "longitud_dms": lon_str,
            "google_maps_url": maps_url
        }
    except Exception:
        return None


def _imprimir_reporte_tecnico(info: Dict[str, Any]) -> None:
    """Imprime el reporte técnico en terminal con formato ordenado."""
    print("\n" + "=" * 78)
    print("                      REPORTE TÉCNICO DE LA IMAGEN")
    print("=" * 78)
    origen = os.path.abspath(info["ruta_archivo"]) if info["ruta_archivo"] else "Captura en Memoria RAM"
    print(f"📁 Origen: {origen}\n")

    print("1. DIMENSIONES Y ESTRUCTURA MATRICIAL (SHAPE):")
    print(f"   • Dimensiones (Alto x Ancho x Canales): {info['alto']} x {info['ancho']} x {info['canales']}")
    print(f"   • Total de Píxeles: {info['total_pixeles']:,} píxeles ({info['megapixeles']:.2f} MP)")
    print(f"   • Tipo de Dato (dtype): {info['dtype']}")
    print(f"   • Profundidad por Canal: {info['bits_por_canal']} bits/canal ({info['itemsize_bytes']} byte(s)/muestra)")
    print(f"   • Profundidad Total por Píxel: {info['bits_por_pixel']} bits/píxel\n")

    print("2. ANÁLISIS DE TAMAÑO (MEMORIA RAM vs. DISCO):")
    print(f"   • Tamaño en Memoria RAM (Matriz Cruda): {info['ram_formateado']}")
    print(f"   • Tamaño del Archivo en Disco: {info['disco_formateado']}")
    if info["ratio_compresion"] is not None:
        print(f"   • Factor de Compresión: {info['ratio_compresion']:.2f}:1")
        print(f"   • Ahorro de Espacio en Disco: {info['porcentaje_ahorro']:.1f}%")
    print("\n   Fundamento Teórico de la Diferencia:")
    for l in info["explicacion_compresion"].split("\n"):
        print(f"   {l}")

    print("\n3. ESPACIO Y ORDEN DE CANALES DE COLOR:")
    print(f"   • Espacio: {info['espacio_color']}")
    for l in info["explicacion_color"].split("\n"):
        print(f"   {l}")
    print("=" * 78)


def _imprimir_reporte_exif(exif: Dict[str, Any]) -> None:
    """Imprime el reporte EXIF en terminal con formato ordenado."""
    print("\n" + "=" * 78)
    print("                     METADATOS EXIF Y GEOLOCALIZACIÓN")
    print("=" * 78)

    if not exif["tiene_exif"]:
        print(f"\n{exif['mensaje']}")
        print("=" * 78)
        return

    print("\n📷 INFORMACIÓN DEL DISPOSITIVO Y CAPTURA:")
    print(f"   • Fabricante: {exif['fabricante'] or 'N/D'}")
    print(f"   • Modelo de Cámara: {exif['modelo'] or 'N/D'}")
    if exif['lente']:
        print(f"   • Lente / Objetivo: {exif['lente']}")
    if exif['software']:
        print(f"   • Software/Firmware: {exif['software']}")
    print(f"   • Fecha y Hora: {exif['fecha_hora'] or 'N/D'}")

    print("\n⚙️ PARÁMETROS FOTOGRÁFICOS DE EXPOSICIÓN:")
    print(f"   • Sensibilidad ISO: {exif['iso'] if exif['iso'] is not None else 'N/D'}")
    print(f"   • Apertura del Diafragma: {exif['apertura_f'] or 'N/D'}")
    print(f"   • Velocidad de Obturación: {exif['tiempo_exposicion'] or 'N/D'}")
    print(f"   • Distancia Focal Real: {exif['distancia_focal'] or 'N/D'}")
    if exif['distancia_focal_35mm']:
        print(f"   • Distancia Focal (Equiv. 35mm): {exif['distancia_focal_35mm']}")
    if exif['balance_blancos']:
        print(f"   • Balance de Blancos: {exif['balance_blancos']}")
    if exif['modo_medicion']:
        print(f"   • Modo de Medición: {exif['modo_medicion']}")

    print("\n🌍 GEOLOCALIZACIÓN (GPS):")
    if exif["gps"]:
        gps = exif["gps"]
        print(f"   • Latitud: {gps['latitud_decimal']:.6f}° ({gps['latitud_dms']})")
        print(f"   • Longitud: {gps['longitud_decimal']:.6f}° ({gps['longitud_dms']})")
        if gps['altitud_m'] is not None:
            print(f"   • Altitud: {gps['altitud_m']:.2f} m s.n.m.")
        print(f"   • Ver en Google Maps: {gps['google_maps_url']}")
    else:
        print("   • No contiene etiquetas de geolocalización GPS.")
    print("=" * 78)


# ==============================================================================
# EJECUCIÓN DIRECTA COMO SCRIPT DE DEMOSTRACIÓN / PRUEBA
# ==============================================================================

if __name__ == "__main__":
    print("""
================================================================================
    FPDI 2026 - Módulo 'adquisicion.py' (Ejecución Interactiva / Test)
================================================================================
    """)
    print("Opciones de prueba:")
    print("  [1] Cargar imagen desde archivo (explorador o ruta)")
    print("  [2] Capturar en vivo desde Webcam (OpenCV)")
    print("  [3] Probar con imagen de muestra")
    print("  [4] Salir")

    opc = input("\nSeleccione una opción [1-4]: ").strip()

    img_demo = None
    path_demo = None

    if opc == "1":
        img_demo, path_demo = cargar_imagen(abrir_dialogo=True, retornar_ruta=True)
        if img_demo is None:
            ruta_manual = input("Ingrese ruta de archivo manualmente: ").strip().strip('"').strip("'")
            if ruta_manual:
                img_demo, path_demo = cargar_imagen(ruta_manual, retornar_ruta=True)
    elif opc == "2":
        img_demo, path_demo = capturar_webcam()
    elif opc == "3":
        # Generar imagen sintética de prueba si no existe
        os.makedirs("muestras", exist_ok=True)
        path_demo = os.path.join("muestras", "patron_prueba_sintetico.png")
        if not os.path.exists(path_demo):
            arr = np.zeros((480, 640, 3), dtype=np.uint8)
            arr[:, :320, 0] = 255
            arr[:, 320:, 2] = 255
            cv2.imwrite(path_demo, arr)
        img_demo, path_demo = cargar_imagen(path_demo, retornar_ruta=True)

    if img_demo is not None:
        # 1. Info técnica
        info = info_imagen(img_demo, ruta_archivo=path_demo, imprimir_reporte=True)
        # 2. Exif
        exif = leer_exif(path_demo, imprimir_reporte=True)
        # 3. Opciones visuales
        ver = input("\n¿Desea ver la descomposición de canales (Original | B | G | R)? [S/n]: ").strip().lower()
        if ver in ["s", "si", "y", "yes", ""]:
            mostrar_canales(img_demo)

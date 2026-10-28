Se dispone de dos adquisiciones del satélite Sentinel-2 (bandas B1 a B12) de la misma región del norte de Misiones, que incluye parte de una ciudad y una porción extensa de una reserva natural, con fechas 03-09-2026 (previa) y 19-09-2026 (posterior). Entre ambas fechas se tiene constancia del paso de un tornado por la zona.

Como ingeniero a cargo del análisis, diseñe un pipeline de procesamiento digital de imágenes que permita:

a) Representación visual. Generar una imagen que muestre lo más fielmente posible el área afectada, pensada para un público no experto (por ejemplo, autoridades o prensa). Debe ser interpretable sin conocimientos de teledetección.

b) Cuantificación. Estimar la superficie afectada (km^2), discriminando, si el criterio lo justifica, entre el área afectada dentro de la reserva y dentro del área urbana.

Para ambos puntos debe: 
1. Describir y justificar cada etapa del pipeline: preprocesamiento, elección de bandas, espacio de color o índices, y método de detección de cambios.

2. Indicar si las composiciones usadas para a o b son iguales o distintas y por qué

3. Explicar como se determinó los umbrales o criterios de separación entre “afectado” y "no afectado" (análisis de histograma, método automático o manual, validación visual, etc.)

4. Explicar como computó el área

5. Presentar una imagen en la que la máscara del área afectada esté superpuesta a la composición de a con leyenda, escala y orientación

6. Discutir resultados, limitaciones y fuentes de error. Proponer una cota de incertidumbre para el área estimada.
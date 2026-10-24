Esta plantilla está hecha para desarrollar los trabajos prácticos correspondientes a la materia Fundamentos del procesamiento de imágenes, correspondiente al último año de Ingeniería en Computación.

* Para cada trabajo práctico tiene su correspondiente branch.
* Para cada ejercicio se tiene dedicado un .tex en el cual desarrollar dentro de partes/.
* Para cada ejercicio, en caso de utilizar imágenes, crear una subcarpeta dentro de img/.
* Para cada ejercicio, puede colocarse su Jupyter dentro de la carpeta code/ (ver code/README.md).
* Siempre antes de comenzar a trabajar traer los cambios actuales con git pull.
* Antes de entregar el trabajo final actualizar la fecha dentro de partes/titulo.



# Razonamiento:
Pueeeeede ser que en las tablas comparativas de separabilidad HSV me de mal porque lo que se mide con las metricas (como Silhouette Score y la Razón de Fisher) se basan en la distancia euclidiana. Estas métricas asumen y benefician a los clústeres que tienen forma esférica o globular.

Una métrica euclidiana tradicional penaliza estos "pilares" porque calcula que un píxel verde muy brillante (en la cima del pilar) y un píxel verde oscuro (en la base) están lejísimos matemáticamente, arruinando el score de cohesión interna del grupo, a pesar de que visualmente es evidente que pertenecen a la misma clase espectral.   En base a este patrón de "pilares alargados separados por valles vacíos", debes evitar algoritmos que busquen esferas (como K-Means, que probablemente cortaría los pilares horizontalmente basándose en el brillo). Te recomiendo los siguientes algoritmos de clusterización:

* **DBSCAN (Density-Based Spatial Clustering of Applications with Noise)**: Es el candidato ideal para este escenario. DBSCAN agrupa los puntos que están densamente empaquetados, sin importar qué forma geométrica tenga el clúster. Como tus tres pilares son muy densos y están rodeados de espacio vacío, DBSCAN rastreará toda la columna de color de arriba hacia abajo y la clasificará como un solo grupo, ignorando la varianza en brillo y saturación.   

* **GMM (Gaussian Mixture Models / Modelos de Mezcla Gaussiana)**: A diferencia de K-Means, GMM utiliza matrices de covarianza completas. Esto significa que el algoritmo "entiende" y se adapta a clústeres que tienen formas elipsoidales o estiradas. GMM modelará perfectamente que la varianza en el eje Hue es minúscula, pero que la varianza en Valor y Saturación es alta, ajustando un elipsoide vertical para cada pilar.

* **Mean Shift**: Este algoritmo no requiere que le digas cuántos clústeres buscar. Funciona encontrando los "modos" o picos de máxima densidad en el espacio. Dado que la distribución de los píxeles converge claramente en el eje Hue, Mean Shift agrupará eficientemente los datos empujándolos hacia el centro de gravedad de cada pilar de color.  

segun axel: 
¿Desvío estándar enorme? El rojo puro está exactamente en el punto donde el círculo de matices "da la vuelta": en la escala de OpenCV, H≈0 y H≈179 representan colores casi idénticos (ambos son rojo), pero numéricamente están en extremos opuestos del rango. Nuestros píxeles rojos "maduros" quedan repartidos entre H cercano a 0 y H cercano a 179, y una métrica basada en media y varianza (como Fisher, o silhouette con distancia euclídea) interpreta eso como altísima dispersión, subestimando dramáticamente qué tan bien separa realmente el matiz.

Esto no es un error de la imagen ni del código: es una propiedad matemática del matiz. H es una variable circular (un ángulo), no una recta numérica, y las estadísticas lineales (media, varianza, distancia euclídea) no están diseñadas para datos circulares.

La corrección: representar el ángulo como sus componentes cartesianas  (cosθ,sinθ)  antes de calcular cualquier estadística, exactamente como se hace con variables circulares en general (hora del día, dirección del viento, etc.). Puro feature engineering...

Moraleja: cuando se trabaje con H (o con cualquier variable angular: dirección, fase, orientación), desconfiar de estadísticas calculadas ingenuamente sobre el valor crudo, y considerar si es necesaria una representación circular antes de aplicar métricas basadas en distancia euclídea.
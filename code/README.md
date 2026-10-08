# Notebooks y Google Colab

Puede referenciarse desde Google Colab un `.ipynb` de GitHub, sin subirlo a Drive. El repositorio es la única fuente del notebook: se desarrolla en local, se sube con git y Colab lo abre directamente desde GitHub. Para tal caso el flujo es el siguiente.

## Flujo

1. **Desarrollar y subir el notebook.** Se trabaja en local (VS Code), dentro de `code/` y en la rama del TP. Después se hace commit y push. El notebook tiene que poder ejecutarse en Colab desde cero (ver [Requisitos del notebook](#requisitos-del-notebook)).

2. **Abrirlo en Colab desde GitHub.** Con el badge "Abrir en Colab" del notebook o con este enlace:

   ```
   https://colab.research.google.com/github/BrianAranda/Informes_FDPI/blob/<rama>/code/<notebook>.ipynb
   ```

   También se puede abrir desde Colab, en *Archivo → Abrir cuaderno → GitHub*, pegando la URL del repositorio y eligiendo la rama.

3. **Ejecutarlo completo.** Con *Entorno de ejecución → Ejecutar todas*. Hay que revisar que no haya errores y que las salidas sean las esperadas.

4. **Guardarlo en GitHub desde Colab.** Con *Archivo → Guardar una copia en GitHub*:
   - Repositorio `BrianAranda/Informes_FDPI`, con la misma rama y la misma ruta (`code/<notebook>.ipynb`), para que reemplace al archivo.
   - Mensaje de commit, por ejemplo `Ejecutado en Colab`.
   - Destildar *Incluir un vínculo a Colaboratory*: el notebook ya tiene su badge, y si queda tildado Colab agrega otra celda al principio.

   La primera vez Colab pide autorización en GitHub, y hace falta ser colaborador del repositorio. Como es público, no hace falta darle acceso a los repositorios privados. Es normal que el diff de este commit sea grande, porque Colab reescribe el formato del JSON.

5. **Traer el commit a local.** Colab hace el commit directamente en GitHub, así que hay que hacer `git pull` antes de seguir trabajando. Mientras el notebook está abierto en Colab, no hay que editarlo en local.

6. **Adjuntar el link en el informe.** Se obtiene el hash del commit de Colab:

   ```bash
   git log -1 --format=%H -- code/<notebook>.ipynb
   ```

   Y se agrega en `partes/anexo.tex`:

   ```latex
   \item <Descripción del ejercicio>:
       \href{https://colab.research.google.com/github/BrianAranda/Informes_FDPI/blob/<hash>/code/<notebook>.ipynb}
       {\textcolor{blue}{<notebook>.ipynb}}
   ```

   En el texto visible los `_` se escriben `\_`. En la URL van sin escapar.

Si el notebook cambia después, se repiten los pasos 2 a 6 para que el link apunte a la versión final.

### ¿Por qué el link del informe usa el hash y no la rama?

El badge del notebook apunta a la rama, así que siempre abre la última versión: sirve mientras se trabaja. El link del anexo apunta al commit, así que siempre abre la versión entregada, aunque la rama cambie después.

### ¿Por qué no subir el notebook desde la PC a Colab?

Porque crea una copia en Drive separada del repositorio: quedan dos versiones para mantener y el link de Drive depende de los permisos de compartir. Además, Colab recibe solo el `.ipynb`, sin los módulos ni las imágenes, que igual hay que traer del repositorio.

## Requisitos del notebook

Colab abre solo el `.ipynb`, sin el resto del repositorio. Para que se pueda ejecutar:

- **Badge en la primera celda de markdown,** apuntando a la rama:

  ```markdown
  [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/BrianAranda/Informes_FDPI/blob/<rama>/code/<notebook>.ipynb)
  ```

- **Celda de clonado al principio.** En Colab clona el repositorio y se ubica en `code/`. En local no hace nada. Hay que cambiar `RAMA` por la del TP:

  ```python
  import os
  import subprocess
  import sys

  if "google.colab" in sys.modules:
      RAMA = "<rama>"
      REPO = "https://github.com/BrianAranda/Informes_FDPI.git"
      DESTINO = "/content/Informes_FDPI"
      if not os.path.isdir(DESTINO):
          subprocess.run(["git", "clone", "--depth", "1", "--branch", RAMA, REPO, DESTINO], check=True)
      os.chdir(f"{DESTINO}/code")
      print("Trabajando en", os.getcwd())
  ```

- **Rutas relativas a `code/`,** por ejemplo `imagenes/ejercicio3/foto.jpeg`. No se usan rutas de la PC.
- **Datos:** las imágenes del ejercicio N van en `code/imagenes/ejercicioN/`. GitHub rechaza archivos de más de 100 MB y avisa desde los 50 MB. Los datos pesados, como las bandas Landsat completas, no se suben: se sube un recorte o el notebook los descarga.
- **Fotos de celular:** hay que quitar los datos GPS del EXIF antes de subirlas, porque el repositorio es público.
- **Librerías:** si se usa alguna que Colab no trae, se instala con `%pip install` en la celda de clonado.

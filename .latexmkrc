# Si se ejecuta "latexmk" sin argumentos, compilar solo main.tex
# (si no, compila TODOS los .tex de la raíz, incluido atajos.tex)
@default_files = ('main.tex');

# Motor: 1 = pdflatex, 4 = lualatex, 5 = xelatex
$pdf_mode = 1;
# %O = opciones que agrega latexmk (jobname, directorios), %S = archivo fuente
# Agregar -halt-on-error para frenar en el primer error
# Agregar -shell-escape si usás minted o svg
$pdflatex = 'pdflatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';

# PDF junto a main.tex, auxiliares en build/
$out_dir = '.';
$aux_dir = 'build';

# Bibliografía: 1 = solo si hay citas y archivo .bib
$bibtex_use = 1;

# Extensiones extra que borra "latexmk -c"
$clean_ext = 'synctex.gz run.xml nav snm vrb acn acr alg glo gls glg ist';

# Glosarios y acrónimos (paquete glossaries). Solo se ejecuta si existen .glo/.acn
add_cus_dep('glo', 'gls', 0, 'run_makeglossaries');
add_cus_dep('acn', 'acr', 0, 'run_makeglossaries');
sub run_makeglossaries {
    my ($base_name, $path) = fileparse($_[0]);
    return system('makeglossaries', '-q', '-d', $path, $base_name);
}

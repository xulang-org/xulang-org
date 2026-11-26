<p align="center">
  <a href="https://xulang.org/es">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-dark.svg">
      <img src="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-light.svg" alt="XU — Código nativo. Intención clara." width="100%">
    </picture>
  </a>
</p>

<h1 align="center">El lenguaje de programación XU</h1>

<p align="center">
  Un lenguaje de sistemas con compilación nativa, propiedad y concurrencia integrada.<br>
  <strong>Gestión determinista de memoria. Sin recolector de basura.</strong>
</p>

<p align="center">
  <a href="https://xulang.org/es/playground"><strong>Probar en el navegador</strong></a> &nbsp; · &nbsp;
  <a href="https://xulang.org/es/docs/start">Leer la guía</a> &nbsp; · &nbsp;
  <a href="https://xulang.org/es/download">Descargar XU</a> &nbsp; · &nbsp;
  <a href="https://github.com/xulang-org/xu">Código del compilador</a>
</p>

<p align="center">
  <a href="README.md">English</a> / <a href="README.zh-CN.md">简体中文</a> / <a href="README.zh-TW.md">繁體中文</a> / <a href="README.ja.md">日本語</a> / <a href="README.ko.md">한국어</a> / <strong>Español</strong> / <a href="README.fr.md">Français</a> / <a href="README.de.md">Deutsch</a> / <a href="README.ru.md">Русский</a> / <a href="README.pt-BR.md">Português</a>
</p>

## Un lenguaje compacto con un flujo claro

XU combina la propiedad y el préstamo verificados en tiempo de compilación con corrutinas ligeras y canales tipados. Compila con antelación (AOT) a código máquina nativo o WebAssembly, gestionando el ciclo de vida de los recursos de manera determinista.

| Decisión de diseño | Qué te ofrece |
| :--- | :--- |
| **Propiedad sin GC** | Verificación de movimientos y préstamos en compilación, tiempos de vida inferidos y limpieza determinista de recursos. |
| **Concurrencia en el lenguaje** | Inicia una corrutina con `xu`; intercambia valores mediante canales `chan` tipados. |
| **Flujo de control visible** | `<<` devuelve un valor, `>>>` lanza un error y `>>> (err) { … }` lo gestiona en el punto de llamada. |
| **Cadena de herramientas integrada** | Compila, ejecuta, verifica, prueba, formatea, genera documentación y utiliza el servidor de lenguaje mediante `xu`. |

## Lee un poco de XU

Dos trabajadores, un canal y una ruta de error explícita:

```xu
@main
#errors

fn score(name string) int {
    if name.len == 0 { >>> errors.new("empty name") }
    << name.len * 10
}

fn worker(name string, results chan int) {
    value := score(name) >>> (err) {
        results <- 0
        <<
    }
    results <- value
}

fn main() int {
    results := chan int{cap: 2}
    xu worker("hello", results)
    xu worker("world", results)
    println(<-results + <-results)
    << 0
}
```

Guárdalo como `main.xu` y ejecuta `xu run main.xu`. Imprime `100`.

`#errors` importa un paquete. `xu worker(...)` inicia una corrutina. Las dos recepciones recogen los resultados; si `score` falla, `>>> (err) { … }` envía un valor alternativo de `0` y sale de esa corrutina.

## Empieza aquí

Explora el [playground en el navegador](https://xulang.org/es/playground) sin instalar nada, o [descarga el SDK](https://xulang.org/es/download) para desarrollo local. Tras la instalación:

```sh
xu --version
xu run main.xu
xu build main.xu -o hello
```

Continúa con la [guía de inicio](https://xulang.org/es/docs/start), la [referencia del lenguaje](https://xulang.org/es/docs/lang/syntax) o los [ejemplos ejecutables](https://github.com/xulang-org/examples).

XU evoluciona activamente en la **serie 0.x**. Consulta [Releases](https://github.com/xulang-org/xu/releases) para los SDK publicados y [estado y limitaciones](https://xulang.org/es/docs/status) para la cobertura de plataformas y entornos de ejecución. El [panel de benchmarks](https://xulang.org/es/benchmarks) registra cargas de trabajo medidas, versiones de compiladores y trazabilidad del código fuente.

Usa [Buscar API](https://xulang.org/api/) para encontrar un paquete o saltar a una declaración en la página actual. Pulsa `/` fuera de un campo de entrada para abrir la búsqueda; las flechas y Enter navegan por los resultados, y Escape la cierra. El directorio de la API se pliega en teléfonos para mantener el contenido accesible. Los encabezados de declaración son enlaces permanentes, y «Copy link» comparte la página o declaración actual.

El índice de la API ofrece accesos directos a tareas comunes, descripciones temáticas y búsqueda en línea de paquetes en la biblioteca estándar, UI y extensiones. Las páginas de paquete comienzan con un explorador de declaraciones: filtra por nombre, propósito o tipo y salta a la firma y documentación completas. Los ejemplos fuente relacionados permanecen plegados hasta que se abren.

## Explora el ecosistema

| Proyecto | Dónde ir |
| :--- | :--- |
| **Lenguaje y compilador** | [xu](https://github.com/xulang-org/xu) — compilador auto-hospedado, biblioteca estándar y herramientas CLI. |
| **Aprender ejecutando** | [examples](https://github.com/xulang-org/examples) — fundamentos del lenguaje, concurrencia, redes, bases de datos y ejemplos de UI. |
| **Bibliotecas e integraciones** | [packages](https://github.com/xulang-org/packages) — controladores de bases de datos, mensajería, almacenamiento e integraciones de servicios. |
| **Soporte de editor** | [vscode-xu](https://github.com/xulang-org/vscode-xu) — resaltado de sintaxis y servidor de lenguaje XU para VS Code y Cursor. |
| **Rendimiento** | [bench](https://github.com/xulang-org/bench) — cargas de trabajo multilenguaje y fuentes de benchmark reproducibles. |
| **Sitio web y documentación** | [xulang-org](https://github.com/xulang-org/xulang-org) — xulang.org, documentación y playground WebAssembly. |

## Construye XU con nosotros

Prueba un ejemplo, informa de un error en el compilador, mejora la documentación o contribuye con una biblioteca. Empieza en los [issues del compilador](https://github.com/xulang-org/xu/issues) o los [issues del sitio web](https://github.com/xulang-org/xulang-org/issues).

Lee la [guía de contribución](CONTRIBUTING.md) y las [reglas compartidas de repositorios](.github/REPOSITORY_RULES.md) antes de contribuir. Los mantenedores pueden seguir la [lista de verificación de configuración de GitHub](.github/GITHUB_SETTINGS.md).

[Sitio web](https://xulang.org/es) · [GitHub](https://github.com/xulang-org) · [X / @xulang_org](https://x.com/xulang_org) · [Licencia MIT](LICENSE)

---

<details>
<summary><strong>Trabajar en xulang.org</strong> — compilación del sitio web, playground y despliegue</summary>

Este repositorio de perfil también contiene el código fuente del sitio web oficial. El sitio selecciona el **SDK XU** publicado indicado en `VERSION`; las compilaciones de desarrollo permanecen separadas.

### Compilación local

Requiere **Python 3.10+**, usando únicamente la biblioteca estándar. Las compilaciones estáticas y las comprobaciones se ejecutan sin XU, Node.js ni repositorios hermanos.

```sh
make build                       # Compilar dist/ y verificar enlaces internos y recursos
make run                         # Vista previa en http://127.0.0.1:8080
make run PORT=18080              # Vista previa en un puerto personalizado
make check                       # Ejecutar la suite de regresión del sitio estático
make build BASE_PATH=/xulang-org # Compilar para una subruta de proyecto
make clean                       # Eliminar dist/ y build/playground/
```

| Ruta | Propósito |
| :--- | :--- |
| `content/{en,zh,...}/` | Documentación, tutoriales, entradas de blog y contenido de API. |
| `templates/` | Plantillas de página, guías de API y selecciones de ejemplos. |
| `www/` | Estilos, scripts, fuentes, iconos y recursos estáticos. |
| `playground/typed/` | Runtime WebAssembly para navegador escrito en XU. |
| `scripts/` | Generador estático, generación de API y validación de lanzamientos. |
| `tests/` | Cobertura de regresión del sitio estático, playground y canales. |
| `brand/` | Recursos de marca y directrices de identidad visual. |

La salida generada va a los directorios ignorados `dist/` y `build/`. Los fragmentos de contenido declaran títulos con `<!--title: ...-->` y se renderizan en rutas de directorio como `docs/start/index.html`.

### Metadatos compartidos del sitio

Los recuentos de paquetes de estado proceden de los inventarios generados `content/{en,zh}/api/index.html`. El generador comprueba que ambos inventarios coincidan y que existan sus páginas de paquete; las páginas de detalle y vista previa de widgets no cuentan en el total de paquetes. Actualiza el inventario de la API con el generador cuando cambien los paquetes.

`templates/releases.json` proporciona las notas de lanzamiento, las entradas recientes en el índice del blog y los enlaces de versión en la barra lateral del blog. Añade ahí las nuevas versiones junto con sus entradas de blog. Las publicaciones históricas anteriores permanecen como contenido editorial. Los banners de inicio, cabecera y pie omiten la identidad de parche del SDK; las páginas de descarga, documentación y API la conservan. Los metadatos estructurados de software siguen identificando con precisión el SDK seleccionado.

La selección manual de idioma guarda la preferencia en `localStorage` y en una cookie `SameSite=Lax` de un año. El enlace de idioma también incluye `?lang=...` para funcionar con el almacenamiento bloqueado. El mapa del sitio omite deliberadamente `lastmod` para evitar implicar cambios editoriales ante recompilaciones sin cambios.

### Contenido de API y ejemplos

Las guías LLM usan `templates/llms/*.md`, ejemplos compartidos del sitio, `VERSION` y `www/benchmarks.json`. Ejecuta `python3 scripts/gen_llms.py` para actualizar las copias `www/llms*.txt`.

La prosa curada reside en `templates/api-guides/{en,zh}/`. La generación de API la combina con las declaraciones del SDK seleccionado. Los ejemplos se importan del repositorio oficial de ejemplos en un commit inmutable; las instantáneas en `www/api-examples/` preservan compilaciones locales y de CI independientes.

Las explicaciones a nivel de función viven en `templates/api-contracts.json`. Las entradas revisadas llevan `source_sha256` y `package_sha256`. Ejecuta ejemplos locales de función con el compilador nativo correspondiente:

```sh
python3 scripts/check-api-examples.py --xu /path/to/selected-sdk/bin/xu
```

Para actualizar declaraciones y ejemplos:

```sh
make api XU_ROOT=/path/to/selected-sdk XU_PACKAGES_ROOT=/path/to/selected-sdk/packages \
  XU_EXAMPLES_ROOT=../examples XU_EXAMPLES_REF=FULL_EXAMPLES_COMMIT_SHA
```

Para actualizar proyectos concretos sin reemplazar otras instantáneas de versión, repite `--examples-project`:

```sh
python3 scripts/gen-api.py --src /path/to/selected-sdk/src --packages /path/to/selected-sdk/packages \
  --examples ../examples --examples-ref FULL_EXAMPLES_COMMIT_SHA \
  --examples-project examples/16_ui_webview/component_workshop \
  --examples-project examples/16_ui_webview/style_gallery
```

### Playground WebAssembly

Usa el SDK correspondiente y Node.js 22+ para compilar y optimizar el runtime de XU a WebAssembly:

```sh
npm ci --ignore-scripts # Instalar el optimizador WASM fijado
make wasm XU_ROOT=/path/to/released-sdk
make check-playground   # Comprobar ejecución real de WASM y ejemplos en Node.js
make check-chan         # Comprobar ejemplos nativos de canales con XU
make build              # Empaquetar el runtime en dist/
```

El playground se ejecuta en el navegador del cliente. La documentación y la página principal no precargan WASM. La memoria lineal comienza con el tamaño emitido por el SDK y puede crecer hasta 256 MiB. `build/playground/build.json` registra tamaños, resumen criptográfico, ajustes del optimizador y límites de memoria.

### Benchmarks y despliegue

Para actualizar benchmarks, descarga una ejecución completa de seis plataformas de Actions y ejecuta:

```sh
python3 scripts/import-benchmarks.py --artifacts DIR --bench-root PINNED_BENCH_CHECKOUT --commit FULL_SHA --run-id ID --date YYYY-MM-DD
python3 scripts/sync_all_benches.py --bench-root PINNED_BENCH_CHECKOUT
python3 scripts/gen-benchmarks.py
```

La versión en `VERSION` controla las descargas, la referencia de la API y el runtime del navegador. El flujo de trabajo de Pages verifica el SHA-256 del SDK publicado, prueba su salida y despliega en GitHub Pages en los push a `main`.

</details>

### API y ejemplos de UI

La [guía de UI en inglés](content/en/docs/ui.html) y la [guía en chino](content/zh/docs/ui.html) documentan el SDK oficial de Xu seleccionado en `VERSION`. Los seis paquetes — `ui`, `ui/draw`, `ui/layout`, `ui/chart`, `ui/widgets` y `ui/webview` — aparecen en la navegación de la API publicada.

Las guías manuscritas viven en `templates/api-guides/{en,zh}/ui*`; los contratos semánticos y descripciones de campos viven en `templates/api-contracts.json`. Ejecuta `make api` con el SDK seleccionado para regenerar las declaraciones.

Para una futura API no publicada, el generador sigue admitiendo una vista previa de desarrollo sin cambiar la versión seleccionada:

```sh
python3 scripts/gen-api.py --src /path/to/development-sdk/src --preview --package ui
make build
make check
```

El playground del navegador incluye una [galería de controles de tres páginas](https://xulang.org/es/playground?example=ui-gallery) que ejecuta lógica Xu de escritorio compartida en WASM sobre Canvas. Consulta la [guía de compilación de UI para navegador](playground/README.md) para la sincronización de fuentes, API soportadas, controles de teclado y límites de reproducción.

La documentación de Widgets sigue la jerarquía **API → UI → Widgets → componente**, con 46 páginas de componentes interactivos cuyas fuentes residen en `playground/examples/widget-*.xu` y se publican mediante `python3 scripts/gen-widget-examples.py`.

La [guía de UI en navegador](https://xulang.org/es/docs/ui/#browser-playground) cubre candidatos de ComboBox, casillas de MultiSelect, preferencias de Popover y gestión del foco en Modal.

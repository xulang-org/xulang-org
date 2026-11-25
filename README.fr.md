<p align="center">
  <a href="https://xulang.org/fr">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-dark.svg">
      <img src="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-light.svg" alt="XU — Code natif. Intention claire." width="100%">
    </picture>
  </a>
</p>

<h1 align="center">Le langage de programmation XU</h1>

<p align="center">
  Un langage système avec compilation native, propriété et concurrence intégrée.<br>
  <strong>Gestion déterministe de la mémoire. Aucun ramasse-miettes.</strong>
</p>

<p align="center">
  <a href="https://xulang.org/fr/playground"><strong>Essayer dans le navigateur</strong></a> &nbsp; · &nbsp;
  <a href="https://xulang.org/fr/docs/start">Lire le guide</a> &nbsp; · &nbsp;
  <a href="https://xulang.org/fr/download">Télécharger XU</a> &nbsp; · &nbsp;
  <a href="https://github.com/xulang-org/xu">Code du compilateur</a>
</p>

<p align="center">
  <a href="README.md">English</a> / <a href="README.zh-CN.md">简体中文</a> / <a href="README.zh-TW.md">繁體中文</a> / <a href="README.ja.md">日本語</a> / <a href="README.ko.md">한국어</a> / <a href="README.es.md">Español</a> / <strong>Français</strong> / <a href="README.de.md">Deutsch</a> / <a href="README.ru.md">Русский</a> / <a href="README.pt-BR.md">Português</a>
</p>

## Un petit langage au flux limpide

XU réunit la propriété et l'emprunt vérifiés à la compilation avec des coroutines légères et des canaux typés. Il compile à l'avance (AOT) vers du code machine natif ou WebAssembly, avec une gestion déterministe de la durée de vie des ressources.

| Choix de conception | Ce que cela vous apporte |
| :--- | :--- |
| **Propriété sans GC** | Vérification des déplacements et emprunts à la compilation, durées de vie inférées et nettoyage déterministe des ressources. |
| **Concurrence intégrée** | Lancez une coroutine avec `xu` ; échangez des valeurs via des canaux `chan` typés. |
| **Flux de contrôle visible** | `<<` renvoie une valeur, `>>` lève une erreur et `or (err) { … }` la gère au point d'appel. |
| **Chaîne d'outils intégrée** | Compilez, exécutez, vérifiez, testez, formatez, générez la documentation et utilisez le serveur de langage via `xu`. |

## Lire un peu de XU

Deux travailleurs, un canal et un chemin d'erreur explicite :

```xu
@main
#errors

fn score(name string) int {
    if name.len == 0 { >> errors.new("empty name") }
    << name.len * 10
}

fn worker(name string, results chan int) {
    value := score(name) or (err) {
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

Enregistrez sous `main.xu`, puis exécutez `xu run main.xu`. Le programme affiche `100`.

`#errors` importe un paquet. `xu worker(...)` démarre une coroutine. Les deux réceptions collectent les résultats ; si `score` échoue, `or (err) { … }` envoie une valeur de repli `0` et quitte ce travailleur.

## Commencer ici

Explorez le [bac à sable navigateur](https://xulang.org/fr/playground) sans rien installer, ou [téléchargez le SDK](https://xulang.org/fr/download) pour le développement local. Après installation :

```sh
xu --version
xu run main.xu
xu build main.xu -o hello
```

Poursuivez avec le [guide de démarrage](https://xulang.org/fr/docs/start), la [référence du langage](https://xulang.org/fr/docs/lang/syntax) ou les [exemples exécutables](https://github.com/xulang-org/examples).

XU évolue activement dans la **série 0.x**. Consultez [Releases](https://github.com/xulang-org/xu/releases) pour les SDK publiés et [statut et limitations](https://xulang.org/fr/docs/status) pour la couverture des plateformes et runtimes. Le [tableau de benchmarks](https://xulang.org/fr/benchmarks) consigne les charges mesurées, versions de compilateurs et sources vérifiées.

Utilisez [Rechercher l'API](https://xulang.org/api/) pour trouver un paquet ou sauter à une déclaration sur la page courante. Appuyez sur `/` hors d'un champ de saisie pour ouvrir la recherche ; les flèches et Entrée parcourent les résultats, Échap la ferme. Le répertoire d'API se replie sur mobile pour garder le contenu accessible. Les titres de déclaration sont des permaliens, et « Copy link » partage la page ou la déclaration courante.

L'index d'API offre des raccourcis de tâches courantes, des descriptions thématiques et une recherche directe parmi la bibliothèque standard, l'UI et les extensions. Les pages de paquets s'ouvrent sur un explorateur de déclarations : filtrez par nom, usage ou genre, puis accédez à la signature complète et à sa documentation. Les exemples sources associés restent repliés jusqu'à leur ouverture.

## Explorer l'écosystème

| Projet | Où aller |
| :--- | :--- |
| **Langage et compilateur** | [xu](https://github.com/xulang-org/xu) — compilateur auto-hébergé, bibliothèque standard et outils CLI. |
| **Apprendre en exécutant** | [examples](https://github.com/xulang-org/examples) — bases du langage, concurrence, réseau, bases de données et exemples UI. |
| **Bibliothèques et intégrations** | [packages](https://github.com/xulang-org/packages) — pilotes de bases de données, messagerie, stockage et intégrations de services. |
| **Support éditeur** | [vscode-xu](https://github.com/xulang-org/vscode-xu) — coloration syntaxique et serveur de langage XU pour VS Code et Cursor. |
| **Performances** | [bench](https://github.com/xulang-org/bench) — charges inter-langages et sources de benchmark reproductibles. |
| **Site web et documentation** | [xulang-org](https://github.com/xulang-org/xulang-org) — xulang.org, documentation et playground WebAssembly. |

## Construire XU avec nous

Essayez un exemple, signalez un bogue du compilateur, améliorez la documentation ou contribuez une bibliothèque. Commencez par les [issues du compilateur](https://github.com/xulang-org/xu/issues) ou les [issues du site web](https://github.com/xulang-org/xulang-org/issues).

Lisez le [guide de contribution](CONTRIBUTING.md) et les [règles communes des dépôts](.github/REPOSITORY_RULES.md) avant de contribuer. Les mainteneurs peuvent suivre la [liste de contrôle des réglages GitHub](.github/GITHUB_SETTINGS.md).

[Site web](https://xulang.org/fr) · [GitHub](https://github.com/xulang-org) · [X / @xulang_org](https://x.com/xulang_org) · [Licence MIT](LICENSE)

---

<details>
<summary><strong>Travailler sur xulang.org</strong> — génération du site, playground et déploiement</summary>

Ce dépôt de profil héberge également les sources du site web officiel. Le site sélectionne le **SDK XU** publié désigné par `VERSION` ; les compilations de développement restent séparées.

### Compilation locale

Nécessite **Python 3.10+**, en utilisant uniquement la bibliothèque standard. Les compilations statiques et vérifications s'exécutent sans XU, Node.js ni dépôts voisins.

```sh
make build                       # Générer dist/ et vérifier les liens internes et ressources
make run                         # Aperçu sur http://127.0.0.1:8080
make run PORT=18080              # Aperçu sur un port personnalisé
make check                       # Lancer la suite de régression du site statique
make build BASE_PATH=/xulang-org # Compiler pour un sous-chemin de projet
make clean                       # Supprimer dist/ et build/playground/
```

| Chemin | Rôle |
| :--- | :--- |
| `content/{en,zh,...}/` | Documentation, tutoriels, articles de blog et contenu API. |
| `templates/` | Gabarits de pages, guides API et sélections d'exemples. |
| `www/` | Styles, scripts, polices, icônes et ressources statiques. |
| `playground/typed/` | Runtime WebAssembly navigateur écrit en XU. |
| `scripts/` | Générateur statique, génération d'API et validation de version. |
| `tests/` | Couverture de régression du site statique, du playground et des canaux. |
| `brand/` | Ressources de marque et charte d'identité visuelle. |

Les fichiers générés sont placés dans les répertoires ignorés `dist/` et `build/`. Les fragments de contenu déclarent leur titre via `<!--title: ...-->` et sont rendus en routes de répertoire comme `docs/start/index.html`.

### Métadonnées partagées du site

Les compteurs de paquets proviennent des inventaires générés `content/{en,zh}/api/index.html`. Le générateur vérifie que les deux inventaires correspondent et que leurs pages de paquets existent.

`templates/releases.json` alimente les notes de version, les entrées récentes de l'index du blog et les liens de version dans la barre latérale. La sélection manuelle de langue est stockée dans `localStorage` et un cookie `SameSite=Lax` valable un an, avec prise en charge de `?lang=...`. Le sitemap omet volontairement `lastmod` afin qu'une recompilation inchangée ne laisse pas entendre un contenu modifié.

### Contenu API et exemples

Les guides LLM reposent sur `templates/llms/*.md`, les exemples partagés, `VERSION` et `www/benchmarks.json`. Exécutez `python3 scripts/gen_llms.py` pour actualiser `www/llms*.txt`.

La rédaction manuelle vit dans `templates/api-guides/{en,zh}/` et les contrats par fonction dans `templates/api-contracts.json`. Exécutez les exemples locaux avec le compilateur natif correspondant :

```sh
python3 scripts/check-api-examples.py --xu /path/to/selected-sdk/bin/xu
```

Pour régénérer les déclarations et exemples :

```sh
make api XU_ROOT=/path/to/selected-sdk XU_PACKAGES_ROOT=/path/to/selected-sdk/packages \
  XU_EXAMPLES_ROOT=../examples XU_EXAMPLES_REF=FULL_EXAMPLES_COMMIT_SHA
```

Pour mettre à jour des projets ciblés sans toucher aux autres instantanés, répétez `--examples-project` :

```sh
python3 scripts/gen-api.py --src /path/to/selected-sdk/src --packages /path/to/selected-sdk/packages \
  --examples ../examples --examples-ref FULL_EXAMPLES_COMMIT_SHA \
  --examples-project examples/16_ui_webview/component_workshop \
  --examples-project examples/16_ui_webview/style_gallery
```

### Playground WebAssembly

Utilisez le SDK correspondant et Node.js 22+ pour compiler et optimiser le runtime XU en WebAssembly :

```sh
npm ci --ignore-scripts # Installer l'optimiseur WASM verrouillé
make wasm XU_ROOT=/path/to/released-sdk
make check-playground   # Vérifier l'exécution réelle WASM et les exemples sous Node.js
make check-chan         # Vérifier les exemples natifs de canaux avec XU
make build              # Intégrer le runtime dans dist/
```

Le playground s'exécute côté client dans le navigateur. La documentation et la page d'accueil ne préchargent pas WASM. La mémoire linéaire démarre à la taille émise par le SDK et peut croître jusqu'à 256 Mio. `build/playground/build.json` enregistre les tailles, empreintes, réglages de l'optimiseur et limites mémoire.

### Benchmarks et déploiement

Pour actualiser les benchmarks, téléchargez une exécution Actions complète sur six plateformes, puis lancez :

```sh
python3 scripts/import-benchmarks.py --artifacts DIR --bench-root PINNED_BENCH_CHECKOUT --commit FULL_SHA --run-id ID --date YYYY-MM-DD
python3 scripts/sync_all_benches.py --bench-root PINNED_BENCH_CHECKOUT
python3 scripts/gen-benchmarks.py
```

La version dans `VERSION` pilote les téléchargements, la référence API et le runtime navigateur. Le workflow Pages vérifie le SHA-256 du SDK publié, teste sa sortie et déploie sur GitHub Pages lors des push sur `main`.

</details>

### API et exemples UI

Le [guide UI anglais](content/en/docs/ui.html) et le [guide chinois](content/zh/docs/ui.html) documentent le SDK officiel Xu sélectionné dans `VERSION`. Les six paquets — `ui`, `ui/draw`, `ui/layout`, `ui/chart`, `ui/widgets` et `ui/webview` — figurent dans la navigation API publiée.

Pour une future API non publiée, le générateur prend en charge un aperçu de développement sans modifier la version sélectionnée :

```sh
python3 scripts/gen-api.py --src /path/to/development-sdk/src --preview --package ui
make build
make check
```

Le playground navigateur inclut une [galerie de contrôles en trois pages](https://xulang.org/fr/playground?example=ui-gallery) exécutant la logique Xu desktop partagée en WASM sur Canvas. Voir le [guide de compilation UI navigateur](playground/README.md) pour la synchronisation des sources, les API supportées, les raccourcis clavier et les limites de relecture.

La documentation Widgets suit **API → UI → Widgets → composant**, avec 46 pages de composants interactifs dont les sources résident dans `playground/examples/widget-*.xu` et sont publiées par `python3 scripts/gen-widget-examples.py`.

Le [guide UI navigateur](https://xulang.org/fr/docs/ui/#browser-playground) détaille les candidats ComboBox, les cases MultiSelect, les préférences Popover et la gestion du focus Modal.

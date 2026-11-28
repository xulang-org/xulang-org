<p align="center">
  <a href="https://xulang.org/pt-br">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-dark.svg">
      <img src="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-light.svg" alt="XU — Código nativo. Intenção clara." width="100%">
    </picture>
  </a>
</p>

<h1 align="center">A Linguagem de Programação XU</h1>

<p align="center">
  Uma linguagem de sistemas com compilação nativa, propriedade e concorrência integrada.<br>
  <strong>Gerenciamento determinístico de memória. Sem coletor de lixo.</strong>
</p>

<p align="center">
  <a href="https://xulang.org/pt-br/playground"><strong>Experimentar no navegador</strong></a> &nbsp; · &nbsp;
  <a href="https://xulang.org/pt-br/docs/start">Ler o guia</a> &nbsp; · &nbsp;
  <a href="https://xulang.org/pt-br/download">Baixar XU</a> &nbsp; · &nbsp;
  <a href="https://github.com/xulang-org/xu">Código do compilador</a>
</p>

<p align="center">
  <a href="README.md">English</a> / <a href="README.zh-CN.md">简体中文</a> / <a href="README.zh-TW.md">繁體中文</a> / <a href="README.ja.md">日本語</a> / <a href="README.ko.md">한국어</a> / <a href="README.es.md">Español</a> / <a href="README.fr.md">Français</a> / <a href="README.de.md">Deutsch</a> / <a href="README.ru.md">Русский</a> / <strong>Português</strong>
</p>

## Uma linguagem enxuta com fluxo claro

XU une propriedade e empréstimo verificados em tempo de compilação com corrotinas leves e canais tipados. Compila antecipadamente (AOT) para código nativo ou WebAssembly, com o ciclo de vida dos recursos gerenciado deterministicamente.

| Escolha da linguagem | O que ela oferece |
| :--- | :--- |
| **Propriedade sem GC** | Verificações de movimentação e empréstimo em compilação, lifetimes inferidos e limpeza determinística de recursos. |
| **Concorrência na linguagem** | Inicie uma corrotina com `xu`; troque valores por canais `chan` tipados. |
| **Fluxo de controle visível** | `<<` retorna um valor, `>>` lança um erro e `>>> (err) { … }` o trata no ponto de chamada. |
| **Toolchain integrada** | Compile, execute, verifique, teste, formate, gere documentação e use serviços de linguagem por meio de `xu`. |

## Leia um pouco de XU

Dois trabalhadores, um canal e um caminho explícito de erro:

```xu
@main
#errors

fn score(name string) int {
    if name.len == 0 { >> errors.new("empty name") }
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

Salve como `main.xu` e execute `xu run main.xu`. A saída será `100`.

`#errors` importa um pacote. `xu worker(...)` inicia uma corrotina. As duas recepções coletam os resultados; se `score` falhar, `>>> (err) { … }` envia um valor reserva de `0` e encerra esse trabalhador.

## Comece aqui

Explore o [playground no navegador](https://xulang.org/pt-br/playground) sem instalar nada, ou [baixe o SDK](https://xulang.org/pt-br/download) para desenvolvimento local. Após a instalação:

```sh
xu --version
xu run main.xu
xu build main.xu -o hello
```

Continue com o [guia de início rápido](https://xulang.org/pt-br/docs/start), a [referência da linguagem](https://xulang.org/pt-br/docs/lang/syntax) ou os [exemplos executáveis](https://github.com/xulang-org/examples).

XU evolui ativamente na **série 0.x**. Veja [Releases](https://github.com/xulang-org/xu/releases) para SDKs publicados e [status e limitações](https://xulang.org/pt-br/docs/status) para cobertura de plataformas e runtimes. O [painel de benchmarks](https://xulang.org/pt-br/benchmarks) registra cargas medidas, versões de compiladores e proveniência do código-fonte.

Use [Pesquisar API](https://xulang.org/api/) para localizar um pacote ou ir diretamente a uma declaração na página atual. Pressione `/` fora de um campo de texto para abrir a busca; setas e Enter navegam pelos resultados, e Escape a fecha. O diretório da API recolhe em celulares para manter o conteúdo acessível. Títulos de declarações são links permanentes, e «Copy link» compartilha a página ou declaração atual.

O índice da API traz atalhos para tarefas comuns, descrições temáticas e busca direta na biblioteca padrão, UI e extensões. As páginas de pacotes começam com um explorador de declarações: filtre por nome, finalidade ou tipo e vá direto à assinatura completa e à documentação. Exemplos relacionados ficam recolhidos até serem abertos.

## Explore o ecossistema

| Projeto | Onde ir |
| :--- | :--- |
| **Linguagem e compilador** | [xu](https://github.com/xulang-org/xu) — compilador auto-hospedado, biblioteca padrão e ferramentas CLI. |
| **Aprenda executando** | [examples](https://github.com/xulang-org/examples) — fundamentos da linguagem, concorrência, rede, bancos de dados e exemplos de UI. |
| **Bibliotecas e integrações** | [packages](https://github.com/xulang-org/packages) — drivers de banco de dados, mensageria, armazenamento e integrações de serviços. |
| **Suporte a editores** | [vscode-xu](https://github.com/xulang-org/vscode-xu) — destaque de sintaxe e servidor de linguagem XU para VS Code e Cursor. |
| **Desempenho** | [bench](https://github.com/xulang-org/bench) — cargas multilíngues e fontes de benchmark reproduzíveis. |
| **Site e documentação** | [xulang-org](https://github.com/xulang-org/xulang-org) — xulang.org, documentação e playground WebAssembly. |

## Construa o XU conosco

Teste um exemplo, relate um problema no compilador, melhore a documentação ou contribua com uma biblioteca. Comece pelas [issues do compilador](https://github.com/xulang-org/xu/issues) ou pelas [issues do site](https://github.com/xulang-org/xulang-org/issues).

Leia o [guia de contribuição](CONTRIBUTING.md) e as [regras compartilhadas dos repositórios](.github/REPOSITORY_RULES.md) antes de contribuir. Mantenedores podem seguir a [lista de verificação de configurações do GitHub](.github/GITHUB_SETTINGS.md).

[Site](https://xulang.org/pt-br) · [GitHub](https://github.com/xulang-org) · [X / @xulang_org](https://x.com/xulang_org) · [Licença MIT](LICENSE)

---

<details>
<summary><strong>Trabalhando no xulang.org</strong> — build do site, playground e implantação</summary>

Este repositório de perfil também contém o código-fonte do site oficial. O site seleciona o **SDK XU** publicado identificado por `VERSION`; compilações de desenvolvimento permanecem separadas.

### Build local

Requer **Python 3.10+**, usando apenas a biblioteca padrão. Builds estáticos e verificações rodam sem XU, Node.js ou repositórios irmãos.

```sh
make build                       # Compilar dist/ e verificar links internos e assets
make run                         # Pré-visualizar em http://127.0.0.1:8080
make run PORT=18080              # Pré-visualizar em porta personalizada
make check                       # Executar a suíte de regressão do site estático
make build BASE_PATH=/xulang-org # Compilar para um subcaminho de projeto
make clean                       # Remover dist/ e build/playground/
```

| Caminho | Finalidade |
| :--- | :--- |
| `content/{en,zh,...}/` | Documentação, tutoriais, postagens do blog e conteúdo de API. |
| `templates/` | Modelos de página, guias de API e seleções de exemplos. |
| `www/` | Estilos, scripts, fontes, ícones e recursos estáticos. |
| `playground/typed/` | Runtime WebAssembly para navegador escrito em XU. |
| `scripts/` | Construtor estático, geração de API e validação de lançamentos. |
| `tests/` | Cobertura de regressão do site estático, playground e canais. |
| `brand/` | Recursos de marca e diretrizes de identidade visual. |

Os arquivos gerados ficam nos diretórios ignorados `dist/` e `build/`. Fragmentos de conteúdo declaram títulos com `<!--title: ...-->` e são renderizados em rotas de diretório como `docs/start/index.html`.

### Metadados compartilhados do site

As contagens de pacotes de status vêm dos inventários gerados `content/{en,zh}/api/index.html`. O construtor verifica se ambos os inventários coincidem e se suas páginas de pacotes existem.

`templates/releases.json` fornece as notas de versão, entradas recentes no índice do blog e links de versão na barra lateral. A seleção manual de idioma fica salva em `localStorage` e em um cookie `SameSite=Lax` de um ano, com suporte a `?lang=...`. O sitemap omite deliberadamente `lastmod` para que uma recompilação sem alterações não sugira conteúdo novo.

### Conteúdo de API e exemplos

Os guias de LLM utilizam `templates/llms/*.md`, exemplos compartilhados, `VERSION` e `www/benchmarks.json`. Execute `python3 scripts/gen_llms.py` para atualizar `www/llms*.txt`.

Os guias curados residem em `templates/api-guides/{en,zh}/` e os contratos por função em `templates/api-contracts.json`. Execute exemplos locais de função com o compilador nativo correspondente:

```sh
python3 scripts/check-api-examples.py --xu /path/to/selected-sdk/bin/xu
```

Para atualizar declarações e exemplos:

```sh
make api XU_ROOT=/path/to/selected-sdk XU_PACKAGES_ROOT=/path/to/selected-sdk/packages \
  XU_EXAMPLES_ROOT=../examples XU_EXAMPLES_REF=FULL_EXAMPLES_COMMIT_SHA
```

Para atualizar projetos individuais sem substituir outros snapshots de versão, repita `--examples-project`:

```sh
python3 scripts/gen-api.py --src /path/to/selected-sdk/src --packages /path/to/selected-sdk/packages \
  --examples ../examples --examples-ref FULL_EXAMPLES_COMMIT_SHA \
  --examples-project examples/16_ui_webview/component_workshop \
  --examples-project examples/16_ui_webview/style_gallery
```

### Playground WebAssembly

Use o SDK correspondente e Node.js 22+ para compilar e otimizar o runtime XU para WebAssembly:

```sh
npm ci --ignore-scripts # Instalar o otimizador WASM fixado
make wasm XU_ROOT=/path/to/released-sdk
make check-playground   # Testar execução real de WASM e exemplos no Node.js
make check-chan         # Testar exemplos nativos de canais com XU
make build              # Empacotar o runtime em dist/
```

O playground roda no cliente, dentro do navegador. A documentação e a página inicial não pré-carregam WASM. A memória linear começa no tamanho emitido pelo SDK e pode crescer até 256 MiB. `build/playground/build.json` registra tamanhos, hash, configurações do otimizador e limites de memória.

### Benchmarks e implantação

Para atualizar os benchmarks, baixe uma execução completa de seis plataformas do Actions e rode:

```sh
python3 scripts/import-benchmarks.py --artifacts DIR --bench-root PINNED_BENCH_CHECKOUT --commit FULL_SHA --run-id ID --date YYYY-MM-DD
python3 scripts/sync_all_benches.py --bench-root PINNED_BENCH_CHECKOUT
python3 scripts/gen-benchmarks.py
```

A versão em `VERSION` controla downloads, referência da API e o runtime do navegador. O workflow Pages verifica o SHA-256 do SDK publicado, testa a saída e publica no GitHub Pages em pushes para `main`.

</details>

### API e exemplos de UI

O [guia de UI em inglês](content/en/docs/ui.html) e o [guia em chinês](content/zh/docs/ui.html) documentam o SDK oficial do Xu selecionado em `VERSION`. Todos os seis pacotes — `ui`, `ui/draw`, `ui/layout`, `ui/chart`, `ui/widgets` e `ui/webview` — aparecem na navegação da API publicada.

Para uma API futura ainda não lançada, o gerador suporta uma pré-visualização de desenvolvimento sem alterar a versão selecionada:

```sh
python3 scripts/gen-api.py --src /path/to/development-sdk/src --preview --package ui
make build
make check
```

O playground no navegador inclui uma [galeria de controles de três páginas](https://xulang.org/pt-br/playground?example=ui-gallery) que executa lógica Xu desktop compartilhada em WASM sobre Canvas. Consulte o [guia de build da UI no navegador](playground/README.md) para sincronização de fontes, APIs suportadas, atalhos de teclado e limites de replay.

A documentação de Widgets segue **API → UI → Widgets → componente**, com 46 páginas de componentes interativos cujos códigos-fonte residem em `playground/examples/widget-*.xu` e são publicados por `python3 scripts/gen-widget-examples.py`.

O [guia de UI no navegador](https://xulang.org/pt-br/docs/ui/#browser-playground) aborda candidatos de ComboBox, caixas de seleção MultiSelect, preferências de Popover e controle de foco em Modal.

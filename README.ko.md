<p align="center">
  <a href="https://xulang.org/ko">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-dark.svg">
      <img src="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-light.svg" alt="XU — 네이티브 코드. 명확한 의도." width="100%">
    </picture>
  </a>
</p>

<h1 align="center">Xu 프로그래밍 언어</h1>

<p align="center">
  네이티브 컴파일, 소유권 모델, 내장 동시성을 갖춘 시스템 언어.<br><strong>결정론적 메모리 관리. 가비지 컬렉터 없음.</strong>
</p>

<p align="center">
  <a href="https://xulang.org/ko/playground"><strong>온라인 플레이그라운드 (무설치)</strong></a> &nbsp; · &nbsp;
  <a href="https://xulang.org/ko/docs/start">30초 빠른 시작</a> &nbsp; · &nbsp;
  <a href="https://xulang.org/ko/download">설치 프로그램 다운로드</a> &nbsp; · &nbsp;
  <a href="https://github.com/xulang-org/xu">컴파일러 소스</a>
</p>

<p align="center">
  <a href="README.md">English</a> / <a href="README.zh-CN.md">简体中文</a> / <a href="README.zh-TW.md">繁體中文</a> / <a href="README.ja.md">日本語</a> / <strong>한국어</strong> / <a href="README.es.md">Español</a> / <a href="README.fr.md">Français</a> / <a href="README.de.md">Deutsch</a> / <a href="README.ru.md">Русский</a> / <a href="README.pt-BR.md">Português</a>
</p>

## 간결한 언어, 명확한 흐름

XU는 컴파일 타임 소유권 및 대여 검사, 경량 코루틴, 타입 안전 채널을 유기적으로 결합한 현대 시스템 프로그래밍 언어입니다. 소스 코드는 AOT를 통해 네이티브 머신 코드 또는 WebAssembly로 컴파일되며, 리소스 수명 주기는 결정론적으로 관리됩니다.

| 언어 설계 | 제공하는 가치 |
| :--- | :--- |
| **GC 없는 소유권 모델** | 컴파일 타임 이동 및 대여 검사, 수명 주기 자동 추론, 결정론적 리소스 정리. |
| **언어 내장 동시성** | `xu`로 경량 코루틴을 시작하고 타입 안전 `chan` 채널을 통해 안전하게 값을 교환. |
| **눈에 보이는 제어 흐름** | `<<`로 값을 반환하고, `>>>`로 오류를 발생시키며, 호출부에서 `>>> (err) { … }`로 명시적 처리. |
| **통합 도구 체인** | `xu` 명령어 하나로 빌드, 실행, 검사, 테스트, 포맷팅, 문서 생성 및 언어 서버 지원. |

## XU 코드 읽어보기

두 개의 작업자 코루틴, 하나의 채널, 명시적인 오류 처리 경로:

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

`main.xu`로 저장한 뒤 `xu run main.xu`를 실행하면 `100`이 출력됩니다.

`#errors`로 패키지를 임포트하고, `xu worker(...)`로 코루틴을 시작합니다. 두 번의 채널 수신으로 결과를 집계하며, `score`가 실패할 경우 `>>> (err) { … }`가 기본값 `0`을 채널로 전송하고 해당 작업자를 종료합니다.

## 여기서 시작하기

설치 없이 브라우저에서 바로 [온라인 플레이그라운드](https://xulang.org/ko/playground)를 체험하거나 로컬 개발을 위해 [SDK를 다운로드](https://xulang.org/ko/download)하세요. 설치 후 다음 명령어를 실행합니다:

```sh
xu --version
xu run main.xu
xu build main.xu -o hello
```

이어서 [시작하기 가이드](https://xulang.org/ko/docs/start), [언어 레퍼런스](https://xulang.org/ko/docs/lang/syntax), 또는 [실행 가능한 공식 예제](https://github.com/xulang-org/examples)를 확인하세요.

XU는 현재 **0.x 시리즈**에서 활발히 진화하고 있습니다. 출시된 SDK는 [Releases](https://github.com/xulang-org/xu/releases)를, 지원 플랫폼 및 런타임 현황은 [상태 및 제한 사항](https://xulang.org/ko/docs/status)을 확인하세요. [벤치마크 대시보드](https://xulang.org/ko/benchmarks)에는 실측 워크로드, 컴파일러 버전, 소스 출처가 기록되어 있습니다.

[API 문서](https://xulang.org/api/)를 열고 "API 검색"을 통해 패키지를 찾거나 페이지 내 선언으로 바로 이동할 수 있습니다. 입력창 밖에서 `/` 키를 눌러 검색창을 열고 방향키와 Enter로 결과를 탐색하며 Escape로 닫습니다. 모바일에서는 목차가 자동으로 접혀 본문을 쾌적하게 읽을 수 있습니다. 선언 제목은 영구 링크이며 "링크 복사"로 현재 페이지나 선언을 공유할 수 있습니다.

API 색인은 자주 찾는 작업 바로가기, 주제별 설명, 표준 라이브러리·UI·확장 패키지 인라인 검색을 제공합니다. 패키지 상세 페이지 상단에는 이름, 목적, 선언 종류별로 필터링할 수 있는 선언 탐색기가 포함되어 있습니다.

## 생태계 둘러보기

| 프로젝트 | 바로가기 |
| :--- | :--- |
| **언어 및 컴파일러** | [xu](https://github.com/xulang-org/xu) — 자체 호스팅 컴파일러, 표준 라이브러리, CLI 도구. |
| **예제로 배우기** | [examples](https://github.com/xulang-org/examples) — 언어 기초, 동시성, 네트워킹, 데이터베이스, UI 예제. |
| **라이브러리 및 연동** | [packages](https://github.com/xulang-org/packages) — 데이터베이스 드라이버, 메시징, 스토리지 및 서비스 연동. |
| **에디터 지원** | [vscode-xu](https://github.com/xulang-org/vscode-xu) — VS Code 및 Cursor용 구문 강조 및 XU 언어 서비스. |
| **성능 및 벤치마크** | [bench](https://github.com/xulang-org/bench) — 언어 간 비교 워크로드 및 재현 가능한 벤치마크 소스. |
| **웹사이트 및 문서** | [xulang-org](https://github.com/xulang-org/xulang-org) — xulang.org 공식 웹사이트, 문서 센터, WebAssembly 플레이그라운드. |

## 함께 XU 만들기

예제를 실행해 보거나, 컴파일러 버그를 제보하거나, 문서를 개선하거나, 라이브러리를 기여해 주세요. [컴파일러 Issues](https://github.com/xulang-org/xu/issues) 또는 [공식 웹사이트 Issues](https://github.com/xulang-org/xulang-org/issues)에서 시작할 수 있습니다.

기여하기 전에 [기여 가이드](CONTRIBUTING.md)와 [공통 저장소 규칙](.github/REPOSITORY_RULES.md)을 확인해 주세요. 관리자는 [GitHub 설정 체크리스트](.github/GITHUB_SETTINGS.md)를 참고하시기 바랍니다.

[공식 웹사이트](https://xulang.org/ko) · [GitHub](https://github.com/xulang-org) · [X / @xulang_org](https://x.com/xulang_org) · [MIT 라이선스](LICENSE)

---

<details>
<summary><strong>xulang.org 개발 참여하기</strong> — 웹사이트 빌드, 플레이그라운드 및 배포</summary>

이 홈 저장소에는 공식 웹사이트의 소스 코드가 포함되어 있습니다. 사이트는 `VERSION`에 지정된 공식 출시 **XU SDK**를 사용하며, 개발 빌드는 별도로 관리됩니다.

### 로컬 빌드

**Python 3.10+** (표준 라이브러리만 사용)가 필요합니다. 정적 사이트 빌드 및 검사에는 XU, Node.js 또는 인접 저장소가 필요하지 않습니다.

```sh
make build                       # dist/ 빌드 및 내부 링크/애셋 검증
make run                         # 미리보기: http://127.0.0.1:8080
make run PORT=18080               # 특정 포트로 미리보기
make check                       # 정적 사이트 회귀 테스트 실행
make build BASE_PATH=/xulang-org  # 하위 경로용 빌드
make clean                       # dist/ 및 build/playground/ 정리
```

| 경로 | 용도 |
| :--- | :--- |
| `content/{en,zh,ko,...}/` | 문서, 튜토리얼, 블로그, API 본문. |
| `templates/` | 페이지 템플릿, API 가이드, 예제 선택 설정. |
| `www/` | 스타일시트, 스크립트, 폰트, 아이콘, 정적 애셋. |
| `playground/typed/` | XU로 작성된 브라우저 WebAssembly 런타임. |
| `scripts/` | 정적 빌더, API 생성 및 릴리스 검증 스크립트. |
| `tests/` | 정적 사이트, 플레이그라운드, 채널 회귀 테스트. |
| `brand/` | 브랜드 애셋 및 비주얼 아이덴티티 가이드라인. |

생성된 출력물은 gitignore 처리된 `dist/` 및 `build/` 디렉터리에 저장됩니다. 콘텐츠 조각은 `<!--title: ...-->`로 제목을 선언하고 `docs/start/index.html`과 같은 디렉터리 라우트로 렌더링됩니다.

### 공유 사이트 메타데이터

`templates/site-metadata.json`은 모든 언어에서 공유되는 사이트 전체 메타데이터를 관리합니다.

- 사이트 이름, 기본 제목, 설명
- 테마 색상, 작성자, 소셜 미리보기 카드 (Open Graph / Twitter)
- 검색 키워드, 다국어 설정 (기본 언어, 지원 언어 목록)
- 언어 전환 네비게이션 (언어별 라벨 및 URL 접두사)
- 소셜 링크 및 라이선스 정보

언어를 추가하거나 수정할 때는 이 메타데이터 파일 및 `scripts/build-static.py`의 언어 설정을 업데이트하세요.

### API 문서 생성

정적 사이트는 `VERSION`에 명시된 공식 SDK의 스냅샷을 사용합니다.

```sh
make api
make api XU_SRC=/path/to/released-sdk/src
```

외부 `examples` 저장소의 UI 예제를 병합하는 경우:

```sh
make api XU_EXAMPLES=/path/to/examples XU_EXAMPLES_REF=FULL_EXAMPLES_COMMIT_SHA
```

### WebAssembly 플레이그라운드

호환되는 SDK와 Node.js 22+를 사용하여 XU 러너를 WebAssembly로 컴파일하고 최적화합니다.
락 파일은 빌드에 사용되는 Binaryen 최적화 도구 버전을 고정합니다. 정적 사이트 빌드 자체에는 Python만 필요합니다.

```sh
npm ci --ignore-scripts # 고정 버전 WASM 최적화 도구 설치
make wasm XU_ROOT=/path/to/released-sdk
make check-playground  # Node.js에서 실제 WASM 및 예제 실행 검증
make check-chan        # XU로 네이티브 채널 예제 검증
make build             # 러너를 dist/에 번들링
```

플레이그라운드는 브라우저 클라이언트에서 동작합니다. 일반 문서 열람 시 WASM을 미리 로드하지 않습니다.

### 벤치마크 및 배포

벤치마크를 갱신할 때 동일한 6개 플랫폼 Actions 아티팩트를 다운로드한 후 다음을 실행합니다:

```sh
python3 scripts/import-benchmarks.py --artifacts DIR --commit FULL_SHA --run-id ID --date YYYY-MM-DD
python3 scripts/gen-benchmarks.py
```

`VERSION`은 다운로드 페이지, API 문서, 브라우저 런타임에서 사용하는 공식 SDK를 지정합니다. Pages 워크플로는 SDK의 SHA-256을 검증하고 빌드 결과물을 테스트한 후 `main`에 푸시될 때 배포합니다.

</details>

### UI API 및 예제

[한국어 UI 가이드](content/ko/docs/ui.html)와 [영어 가이드](content/en/docs/ui.html)는 `VERSION`에 선정된 공식 Xu SDK에 대응합니다. `ui`, `ui/draw`, `ui/layout`, `ui/chart`, `ui/widgets`, `ui/webview` 6개 패키지 모두 공식 API 네비게이션에 포함되어 있습니다.

브라우저 플레이그라운드에서는 [3페이지 컨트롤 갤러리](https://xulang.org/ko/playground?example=ui-gallery)를 제공합니다.

Widgets 문서는 **API → UI → Widgets → 컴포넌트** 구조로 구성되어 있습니다. `templates/widgets.json`에서 분류, 사용법, 경험 설명을 관리하며 `scripts/gen-widgets.py`가 공식 선언과 결합하여 페이지를 생성합니다.

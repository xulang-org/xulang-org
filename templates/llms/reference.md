## Additional syntax examples

Each block is a complete independent program from the site's playground examples or ownership tutorial. Save one at a time as `main.xu`.

### Bindings and mutability

{{example:bindings}}

### Structs and methods

{{example:structs}}

### Borrowing

`&T` denotes a shared borrow; `$&T` denotes an exclusive mutable borrow. Follow compiler diagnostics for inferred ownership and borrow lifetimes.

{{example:ownership}}

### Loops and control flow

`<-` breaks a loop and `->` continues it. `<<` returns from a function; `<<<` exits the process.

{{example:loop_control}}

## Project manifest and dependency workflow

Place the project beside the extracted SDK directory named `xu-v{{xu_version}}`, or adjust the local path below to the installed SDK's packages directory:

```xun
module: myapp
version: !ver 0.1.0
xu: !ver {{xu_version}}
require:
  "github.com/xulang-org/packages": file:../xu-v{{xu_version}}/packages
```

From the project root, run:

```sh
xu install
xu check main.xu --offline
xu build main.xu --frozen -o app
```

Commit the application manifest and lockfile for reproducibility. For fetching the SDK's exact source commit instead of using a local bundle, follow https://xulang.org/docs/packages/. Native bridge artifacts may require separate preparation; installing Xu source dependencies does not build those artifacts.

## Tests

Save this as `test.example.xu`:

```xu
@main

fn test_add() {
    assert(1 + 1 == 2)
}
```

Run `xu test test.example.xu -v`. Benchmark functions follow the same filename and signature restrictions, use the `bench_` prefix, and are selected with `-bench REGEXP`.

## Native container metadata

The product `xu native pack` writes top-level `abi`, `format`, `module`, and `slices` metadata. Export signatures are stored in each slice's XUOBJ metadata. The source-tree Python helper `scripts/xunative.py` also retains fields copied from its input manifest, including `exports`; consumers must not assume every product-generated container has top-level `exports`.

Packing multiple target slices and linking a native executable are separate capabilities. The one-step macOS link path needs the macOS C toolchain. For other targets, emit XUOBJ with `--emit-obj`, convert to a platform object, and use the target's external linker. See https://xulang.org/docs/native/ for platform scope.

## Local AI inference and numerical APIs

These features are available in Xu 0.14.3 using the matching compiler and standard library (built-in Mach-O ad-hoc signing requires no manual `codesign` on Apple Silicon). In the Xu source repository, set `XU` to your installed or built compiler and build from the repository root.

```sh
XU_STDLIB_ROOT="$PWD/src" "$XU" build --tensor-fusion examples/llm_engine/main.xu -o llm_engine
# (or XU_TENSOR_FUSION=1 XU_TENSOR_FAST_MATH=1; --tensor-fast-math unlocks fast reductions)
```

```sh
./llm_engine generate ./model.gguf 'ids:1,7,42' 16 0 40 --threads 4 --ctx 128 --kv-dtype f16 --top-p 900 --min-p 50 --repeat-penalty 1100 --presence-penalty 100 --frequency-penalty 50 --seed 42
./llm_engine serve ./model.gguf 127.0.0.1:8080 --threads 4 --kv-dtype bf16 --max-slots 4 --api-key secret
```

The `#tensor` module provides `F16`, `BF16`, four `FP8` variants (`Fp8E4M3Fn`, `Fp8E5M2`, `Fp8E4M3Fnuz`, `Fp8E5M2Fnuz`), `dequant_f16_to_f32`, `dequant_bf16_to_f32`, `TensorView` (`reshape`, `permute`, `read_f32_bytes`, `write_f32_bytes`), `Q4Block`/`Q5Block`/`Q8Block`/`Q4KBlock`/`Q5KBlock`/`Q6KBlock` (`read_q4_k`, `read_q5_k`, `read_q6_k`, `Q8_K_BYTES`, `dot_*_bytes_f32`, `dot_*_row_f32`, `quantize_q5_0_row`, `quantize_q8_k_row`, `dot_q4_k_q8_k_row_f32`, `dot_q5_k_q8_k_row_f32`, `dot_q6_k_q8_k_row_f32`), and 47 pure-Xu primitives (`dot_f32`, `axpy_f32`, `vadd_f32`, `vsub_f32`, `vmul_f32`, `vscale_f32`, `silu_f32`, `gelu_f32`, `rmsnorm_f32`, `add_rmsnorm_f32`, `layernorm_f32`, `l2_normalize_f32`, `cosine_similarity_f32`, `topk_cosine_f32`, `softmax_f32`, `log_softmax_f32`, `swiglu_f32`, `geglu_f32`, `moe_router_f32`, `conv1d_causal_step_f32`, `ssm_scan_step_f32`, `linear_attn_step_f32`, `conv2d_patch_embed_f32`, `mha_sdpa_f32`, `avg_pool2d_f32`, `rope_f32`, `rope_interleaved_f32`, `rope_yarn_f32`, `matvec_f32`, `matmul_f32`, `argmax_f32`, `topk_f32`, `quantize_q8_0`, `quantize_q4_0_row`, `cross_entropy_grad_f32`, `adamw_step_f32`, `lora_add_f32`, `lora_backward_f32`, `rmsnorm_backward_f32`, `layernorm_backward_f32`, `swiglu_backward_f32`, `softmax_backward_f32`, `grad_clip_norm_f32`, `kl_div_grad_f32`, `dpo_loss_grad_f32`, `ppo_clip_grad_f32`, `grpo_advantages_f32`). On `examples/llm_engine/` (`main.xu` + pure-stdlib `models`/`vision`/`gbnf`/`quantize` subpackages), the engine adds `--threads N` multi-threaded CPU inference via the M:N scheduler, `inspect`, local `models list|rm|pull` (`hf://org/repo/file`, `--models-dir`), native Multimodal VLM (`--mmproj` supporting both `mmproj.gguf` F32/F16/BF16 and SafeTensors ViT+MLP, PNG/JPEG/PPM/BMP/base64/`rgb:`, bilinear resize, configurable `image_mean`/`image_std`, `http(s)://` `image_url`, inline `<image>` interleaving), offline HF-sharded/single SafeTensors & GGUF `quantize` (`--type q4_0|q8_0|q4_k|q5_k|q6_k|q4_k_m|q5_k_m`), loads HuggingFace model directories (`config.json`, single or sharded `model.safetensors.index.json`, `tokenizer.json`, `tokenizer_config.json`, F32/F16/BF16/FP8), single-file Safetensors, `VocabIndex` Trie + `GbnfMaskCache` GBNF & JSON Schema grammar constrained decoding (CLI `--grammar`/`--json-schema`/`--gbnf-max-branches` supporting `$ref`/`$defs`/`allOf`/`pattern` & HTTP `grammar`/`response_format`/`text.format`), PEFT SafeTensors LoRA adapters (`--lora`, `--lora-scale`, offline `merge-lora`), sliding-window `perplexity` (`--stride`), pure-Xu SFT `train-lora`/`train-dpo`/`train-grpo`/`train-rlvr`/`train-distill`, lossless `--draft` speculative decoding, Mamba SSM & Hybrid Attention+SSM GGUF, GGUF v2/v3 (`F32`/`F16`/`BF16`/`FP8`/`Q4_0`/`Q4_1`/`Q5_0`/`Q5_1`/`Q8_0`/`Q2_K`–`Q8_K` + `--q8k-act`, DeepSeek MLA, MoE + shared experts, YaRN RoPE), paged KV caches (`--kv-dtype`), SentencePiece + GPT-2 BPE merges, $O(L)$ sampling, and a continuous-batching HTTP server serving OpenAI (`/v1/completions`, `/v1/chat/completions`, stateful `POST /v1/responses`, `/v1/embeddings`), Anthropic (`/v1/messages`), Ollama (`/api/tags`, `/api/generate`, `/api/chat` sync & `application/x-ndjson`), and Prometheus `GET /metrics`.

`--tensor-fusion` / `XU_TENSOR_FUSION=1` enables pattern matching for eligible Xu loops on optimized native ARM64 (NEON/SDOT) and x64 (SSE2/SSSE3) targets including K-quant SIMD kernels, `__xu_tensor_vsub_f32`, `__xu_tensor_vmul_f32`, `gemm4x8_q8_0_p4k4`, and paged attention across `head_dim % 4 == 0`. `--tensor-fast-math` / `XU_TENSOR_FAST_MATH=1` permits floating-point reassociation or fused multiply-add in eligible kernels. `github.com/xulang-org/packages` (`v1.17.0`, 50 packages) provides multi-backend GPU packages (`gpu` unified facade `BACKEND_METAL`/`CUDA`/`VULKAN`/`CPU`, `llm_metal` Apple Silicon GPU Transformer inference & `MetalLoRA` training, `metal`/`metal_native` 176 symbols + Metal K-quant SIMD GEMV, pure-Xu `dlopen` `cuda_native`, pure-Xu `dlopen` + SPIR-V 1.0 `vulkan_native`), alongside `v1.16.0`-hardened `synth`, `openai` (11 presets), `cohere`, `gateway` (`ProviderPassthrough` + Redis distributed state `set_redis_pool`/`set_redis_url`/`set_cache_ttl`), `prompt`, `anthropic`, `gemini`, `mcp` (`2025-03-26`), `a2a` (`set_api_key`/`set_auth_hook` + `set_sqlite_store` + SSE `tasks/sendSubscribe`), `agent` (4-runtime parity, cross-provider `AgentSwarm` `add_anthropic_member`/`add_gemini_member`/`add_responses_member`, pluggable `set_token_counter`, SQLite memory/session/graph checkpoints, `SKILL.md` skills, parallel HITL `StateGraph`, OTLP/Prometheus), `guardrails` (`strict_policy`, `normalize_for_detection`, `check_input_strict`), `eval` (`evaluate_json_schema_raw`, `pass_at_k`, Ragas triad, LLM judges), `rag` (`PgVectorPool` pooled pgvector, `PgVectorClient`, cached `SqliteVectorStore`, `QdrantVectorStore`, GraphRAG `KnowledgeGraph`), `postgres`, `sqlite` (`sqlite_native` pure-Xu `dlopen`), `qdrant`, `milvus`, and `chroma`.

Known AI boundaries and caveats:
- `examples/llm_engine` runs multi-threaded CPU (`--threads N`, not wired directly to `llm_metal` or CUDA); use `packages/llm_metal` for Apple Silicon GPU inference or `packages/gpu` (`metal` / `cuda_native` / `vulkan_native` / CPU fallback) for multi-backend GPU ops.
- GGUF supports K-quants (`Q2_K`–`Q8_K`) and `Q4_1`/`Q5_1`, while imatrix `IQ1`–`IQ4` remain unsupported; image decoding covers PNG/JPEG/PPM/24-bit BMP; training targets single-node `f32` LoRA fine-tuning.
- Since `Xu 0.14.3`, `xu build` embeds Mach-O `LC_CODE_SIGNATURE` ad-hoc signatures automatically (no manual `codesign` required on Apple Silicon).
- In `packages`: `PgVectorPool` adds pooled pgvector queries while `PgVectorClient` retains single-conn compatibility; `rag.SqliteVectorStore` scans loaded rows in memory ($O(N)$ exact search, best under ~10k chunks; use `PgVectorPool` or `QdrantVectorStore` at scale); `gateway` SSE failover applies before the first chunk arrives; terminate TLS/RBAC in front of `a2a`; and pair `guardrails.strict_policy` with `check_safety_openai` against obfuscated evasion.

- With `#math`, `math.float16_to_f32(h int) f32` converts the IEEE 754 binary16 bit pattern in the low 16 bits of `h`. The pattern `0x3e00` converts to `1.5`. See https://xulang.org/api/math/#preview-float16_to_f32.
- `slice.reserve(n int)` is a built-in method on a mutable dynamic slice. It reserves capacity for at least `n` elements and preserves length and values. Pass a nonnegative element count. See https://xulang.org/api/slices/#reserve.
- `slice.resize_zero(n int)` is a built-in method on a mutable dynamic slice of integers, floats, or booleans. It preserves the prefix, zero-initializes the added elements when growing, and retains capacity when shrinking. See https://xulang.org/api/slices/#resize_zero.

## Standard library and integrations

The API catalog at https://xulang.org/api/ is generated from the selected released SDK. It covers formatting, errors, collections, text and encodings, files and processes, networking, cryptography, SQL, and the `ui`, `ui/draw`, `ui/layout`, `ui/widgets`, and `ui/webview` packages. Consult each package's documented target limits.

### Standard library package directory

- `#fmt`: Formatted I/O, string formatting, `println`, `sprint`
- `#strings`: UTF-8 string manipulation, splitting, trimming, and searching
- `#bytes`: Byte buffer operations, slice manipulations, and dynamic buffers
- `#strconv`: String conversion to int, float, bool, and numeric formatting
- `#unicode`: Unicode UTF-8 and UTF-16 character classifications and conversions
- `#regexp`: Regular expressions parsing and pattern matching
- `#net`: TCP, UDP, raw IP socket networking, `listen_on`, `dial`, `listen_packet`
- `#net/http`: High-concurrency multi-worker HTTP server and client, HTTP/2 HPACK decoding
- `#io`: Stream primitives, Reader/Writer interfaces, and filesystem abstractions
- `#os`: System calls, process spawning, signals, environment variables
- `#sync`: Mutex, WaitGroup, Once, and atomic primitives
- `#sync/pool`: M:N scheduler concurrency (`set_max_procs`, `max_procs`, `new_thread_pool`)
- `#tensor`: Low-precision scalar types, strided `TensorView`, GGML blocks, and 47 pure-Xu AI primitives
- `#core/*`: Freestanding kernel & UEFI substrate (`arch`, `sync`, `task`, `virtio`, `uefi`, `acpi`, `pci`, `fdt`, `elf`, `mmio`, `mem`, `alloc`)
- `#time`: Wall-clock time, monotonic duration, timers, tickers, and sleep
- `#runtime`: Compiler runtime statistics, allocator inspection, coroutine scheduling
- `#database/sql`: SQL driver interfaces and connection pooling
- `#crypto/sm4`, `#crypto/sm2`, `#crypto/sm3`, `#crypto/sm9`, `#crypto/zuc`: ShangMi national standard algorithms
- `#crypto/aes`, `#crypto/rsa`, `#crypto/sha256`, `#crypto/tls`: International cryptographic algorithms and TLS
- `#ui`, `#ui/widgets`, `#ui/draw`, `#ui/layout`, `#ui/webview`: Declarative retained-mode UI and GPU canvas

### Networking patterns (TCP / UDP)

```xu
@main
#net

fn run_tcp_server() {
    ln := net.listen_on("tcp", "127.0.0.1:8080") >>> (err) { << }
    c := ln.accept() >>> (err) { << }
    buf := c.read(4096) >>> (err) { << }
    c.write(&buf) >>> (err) { << }
}
```

Official service integrations live in the independent https://github.com/xulang-org/packages repository. The website documents the SDK's pinned package snapshot, which can differ from that repository's current branch. Read the relevant API and example before assuming a protocol feature or native target is supported.

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

These features are available in Xu 0.14.1 using the matching compiler and standard library. In the Xu source repository, set `XU` to your installed or built compiler and build from the repository root.

```sh
XU_STDLIB_ROOT="$PWD/src" "$XU" build --tensor-fusion examples/llm_engine/main.xu -o llm_engine
# (or XU_TENSOR_FUSION=1 XU_TENSOR_FAST_MATH=1; --tensor-fast-math unlocks fast reductions)
```

On macOS ARM64, sign the executable locally with `codesign -fs - ./llm_engine` before running it.

```sh
./llm_engine generate ./model.gguf 'ids:1,7,42' 16 0 40 --ctx 128 --kv-dtype f16 --top-p 900 --min-p 50 --repeat-penalty 1100 --presence-penalty 100 --frequency-penalty 50 --seed 42
./llm_engine serve ./model.gguf 127.0.0.1:8080 --kv-dtype bf16 --max-slots 4 --api-key secret
```

The `#tensor` module provides `F16`, `BF16`, four `FP8` variants (`Fp8E4M3Fn`, `Fp8E5M2`, `Fp8E4M3Fnuz`, `Fp8E5M2Fnuz`), `dequant_f16_to_f32`, `dequant_bf16_to_f32`, `TensorView` (`reshape`, `permute`, `read_f32_bytes`, `write_f32_bytes`), `Q4Block`/`Q5Block`/`Q8Block`/`Q4KBlock`/`Q5KBlock`/`Q6KBlock` (`read_q4_k`, `read_q5_k`, `read_q6_k`, `Q8_K_BYTES`, `dot_*_bytes_f32`, `dot_*_row_f32`, `quantize_q5_0_row`, `quantize_q8_k_row`, `dot_q4_k_q8_k_row_f32`, `dot_q5_k_q8_k_row_f32`, `dot_q6_k_q8_k_row_f32`), and 37 pure-Xu primitives (`dot_f32`, `axpy_f32`, `vadd_f32`, `vsub_f32`, `vmul_f32`, `vscale_f32`, `silu_f32`, `gelu_f32`, `rmsnorm_f32`, `add_rmsnorm_f32`, `layernorm_f32`, `l2_normalize_f32`, `cosine_similarity_f32`, `topk_cosine_f32`, `softmax_f32`, `log_softmax_f32`, `swiglu_f32`, `geglu_f32`, `moe_router_f32`, `rope_f32`, `rope_interleaved_f32`, `rope_yarn_f32`, `matvec_f32`, `matmul_f32`, `argmax_f32`, `topk_f32`, `quantize_q8_0`, `quantize_q4_0_row`, `cross_entropy_grad_f32`, `adamw_step_f32`, `lora_add_f32`, `lora_backward_f32`, `rmsnorm_backward_f32`, `layernorm_backward_f32`, `swiglu_backward_f32`, `softmax_backward_f32`, `grad_clip_norm_f32`). On `examples/llm_engine/main.xu`, the engine loads HuggingFace model directories (`config.json`, single or sharded `model.safetensors.index.json`, `tokenizer.json`, `tokenizer_config.json`, F32/F16/BF16/FP8), single-file Safetensors, PEFT SafeTensors LoRA adapters (`--lora`, `--lora-scale`), pure-Xu `train-lora` fine-tuning (`--lora-rank`, `--lora-alpha`, `--steps`, `--lr`, `--max-grad-norm`), lossless target-verified speculative decoding (`--draft`, `--draft-k`), and compatible GGUF v2/v3 (mixed `Q4_K_M` & `Q5_K` with `Q4_K`/`Q5_K`/`Q6_K` and `--q8k-act` integer K-quant dots, F32/F16/BF16/FP8/Q4_0/`Q5_0`/`Q8_0` `p4k4` SIMD, DeepSeek-V2/V3/R1 MLA with `kv_lora_rank`/`q_lora_rank`/`qk_nope_head_dim`/`qk_rope_head_dim`/`v_head_dim`, full MoE 3D packed & split experts + shared experts, YaRN RoPE scaling, and GGUF metadata), supports optional `qk_norm`, auto-detected multi-template chat (ChatML, Llama-3, Gemma, Mistral), paged KV caches in F32/F16/BF16/FP8 (`--kv-dtype`), SentencePiece + GPT-2 BPE merges, $O(L)$ sampling (`--min-p`, `--presence-penalty`, `--frequency-penalty`, unbounded `top_k`, `logit_bias`), and a multi-slot continuous-batching HTTP server serving OpenAI (`/v1/completions`, `/v1/chat/completions` with `<think>` `reasoning_content` sync+SSE, `tools` -> `tool_calls` sync + SSE `delta.tool_calls`, `response_format`, `logprobs`, stateful `POST /v1/responses` with `instructions`/`previous_response_id`/`tools`/SSE, batch `/v1/embeddings`) and Anthropic Messages API (`/v1/messages` sync+SSE with `thinking`/`text`/`tool_use` + `tool_result` and `x-api-key` auth).

`--tensor-fusion` / `XU_TENSOR_FUSION=1` enables pattern matching for eligible Xu loops on optimized native ARM64 (NEON/SDOT) and x64 (SSE2/SSSE3) targets. Use Xu loops in application code. The compiler manages the `__xu_tensor_*` helpers (including `__xu_tensor_vsub_f32`, `__xu_tensor_vmul_f32`, `gemm4x8_q8_0_p4k4` parity, and paged attention across `head_dim % 4 == 0`). `--tensor-fast-math` / `XU_TENSOR_FAST_MATH=1` permits floating-point reassociation or fused multiply-add in eligible kernels, which can change low bits. On macOS, `github.com/xulang-org/packages` (`v1.9.0`, 37 packages) provides `metal` GPU compute (176 symbols across 6 `.xulib` slices, `gemm_f32_tn`, `paged_kv_cache_append_f16`, `paged_attention_decode_f16`, `gemv_q5_k_f32`, `moe_gemv_q4_k_f32`/`moe_gemv_q5_k_f32`/`moe_gemv_q6_k_f32`, `lora_add_f32`/`adamw_step_f32`/`cross_entropy_grad_f32`/`rmsnorm_backward_f32`/`swiglu_backward_f32`, `Q4Matrix`/`Q5Matrix`/`Q8Matrix`/`Q4KMatrix`/`Q5KMatrix`/`Q6KMatrix`, `simd_sum`/`simd_max` norms/softmax/quant GEMV, online FlashAttention `causal_attention_f32`/`f16` & FlashDecode `attention_decode_f32`/`f16`, `rope_interleaved_f32`, `rope_yarn_f32`, `kv_cache_append_f16`, `add_rmsnorm_f32`, `geglu_f32`, `silu_f32`, `log_softmax_f32`, `moe_topk_f32`, `moe_weighted_add_f32`, fused `moe_gemv_q4_0_f32`/`moe_gemv_q8_0_f32`), alongside pure-Xu `openai` (`clone_client`, Chat, Responses `/v1/responses` sync+SSE `responses`/`responses_stream` & structured `input_json`, vision `ContentPart`, `json_schema_format`, `extra_body_json`, `/v1/completions`, retries, streaming `tool_calls` merge, `reasoning_content`), `anthropic` (`clone_client`, `/v1/messages`, vision `image_base64_block`/`image_url_block`, prompt caching `cache_control`/`cache_system`, `thinking_delta`, chunked `tool_use`, `429`/`529` retries), `gemini` (Google Gemini `clone_client`, `generate`/`generate_stream`/`embed`/`batch_embed`, `inline_data_part`, `functionCall`, `thoughts`, `response_schema_json`), bidirectional `mcp` (JSON-RPC 2.0 `2025-03-26` stdio & Streamable HTTP clients/servers, `ToolAnnotations`, `ResourceTemplateInfo`, `add_resource_template_handler`, `completion/complete`, `logging/setLevel`/`set_logging_level`, `clone_client`, `close_session`, SSE negotiation), `agent` (`Agent` + `ResponsesAgent` + `AnthropicAgent` + `GeminiAgent`, stateful `Session`/`ResponsesSession`/`AnthropicSession`/`GeminiSession`, `set_tool_hook` guardrails, `set_max_total_tokens` budgets, `AgentEvent` `run_stream*`/`send_stream*`, `set_parallel_tools(bool)` via `xu` goroutines, `Step.is_error`), and `rag` (`delete_doc`, `chunk_text`, `chunk_markdown`, `MemoryStore` with dense `topk_cosine_f32`, metadata-filtered `search_by_meta`/`search_hybrid_by_meta`, `rerank_hits`, MMR `search_mmr`, sparse Okapi BM25 `search_bm25`/`search_bm25_filtered`, and RRF hybrid `search_hybrid`/`search_hybrid_filtered`/`retrieve_hybrid`, `save_json`/`load_json`).

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

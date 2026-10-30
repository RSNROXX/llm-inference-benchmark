# LLM Inference Benchmark: Manual Runs (Day 1)

## Setup

| Item | Value |
|---|---|
| Date | 2026-10-23 |
| Machine | Acer Predator laptop, Ubuntu (dual boot) |
| GPU | NVIDIA GeForce RTX 4070 Laptop GPU, 8 GB VRAM (8188 MiB), 80 W cap |
| Driver / CUDA | 595.99.02 / CUDA 13.2 |
| Runtime | Ollama (systemd service, llama.cpp runner) |
| Model | llama3.2:3b (ID a80c4f17acd5) |
| Model size in VRAM | 2.6 GB, 100% GPU (from `ollama ps`) |
| Context window | 4096 tokens |
| Prompt | "Explain docker in 3 sentences." |
| Power source | Plugged in (all runs) |
| Power mode | Run 1: Balanced (default); runs 2 and 3: Performance |
| GPU state before run 1 | P8 (idle, lowest power state), 13 MiB used |

## Results

| Run | Situation | Prompt tokens | Prompt time | Prompt rate | Output tokens | Output time | Output rate | Total |
|---|---|---|---|---|---|---|---|---|
| 1 | Cold start (first request), Balanced | 33 | 15.743 s | 2.10 tok/s | 100 | 2.520 s | 39.68 tok/s | 18.278 s |
| 2 | Warm GPU, Performance | 32 | 42.68 ms | 749.77 tok/s | 95 | 947.3 ms | 100.28 tok/s | 0.993 s |
| 3 | Warm GPU + KV cache (same chat), Performance | 143 (126 cached, 17 new) | 14.12 ms | 1204.05 tok/s | 65 | 674.5 ms | 96.37 tok/s | 0.699 s |

Note: in run 3, the prompt rate is calculated on the 17 uncached tokens only (17 tokens / 14.12 ms = 1204 tok/s).

## Observations

1. **Cold start dominates the first request.** Prompt processing took 15.7 s for 33 tokens (2.1 tok/s). The model was already loaded (load duration ~1 ms), so the delay comes from GPU warm-up (leaving the P8 power state, CUDA setup), not from loading weights.
2. **Run 1 vs run 2:** prompt processing about 350x faster, output generation about 2.5x faster, total time about 18x faster. Caveat: two things changed at once (warm-up AND power mode Balanced to Performance), so this difference cannot yet be attributed to warm-up alone.
3. **Prompt processing is much faster than generation once warm** (750 vs 100 tok/s): the prompt is processed in parallel, while output tokens are generated one at a time.
4. **KV cache in chat mode:** Ollama reused 126 of 143 prompt tokens from the previous turn, so only 17 new tokens had to be processed. Effective prompt time dropped to 14 ms.
5. **Output speed is stable when warm** (~96 to 100 tok/s for a 3B model).

## Implications for the benchmark script

- Do 2 warm-up requests per configuration and discard them.
- Send each measured request without chat history (fresh context), so the KV cache does not distort results.
- Measure caching separately as its own experiment (same long prompt, with and without cache, compare time to first token).
- Record power source and power mode for every run.
- Separate the two effects with a controlled retest: (a) cold start in Performance mode, (b) warm runs in Balanced mode. Change only one variable at a time.
- Planned variables: model (llama3.2:1b, llama3.2:3b, an 8B model in 4-bit), prompt length (short, medium, long).
- Planned metrics: time to first token, prompt tok/s, output tok/s, total time, VRAM used.

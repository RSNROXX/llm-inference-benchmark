# LLM Inference Benchmark: Notes

## Setup

| Item | Value |
|---|---|
| Machine | Acer Predator laptop, Ubuntu (dual boot) |
| GPU | NVIDIA GeForce RTX 4070 Laptop GPU, 8 GB VRAM (8188 MiB) |
| Driver / CUDA | 595.99.02 / CUDA 13.2 |
| Runtime | Ollama (systemd service, llama.cpp runner) |
| Model | llama3.2:3b (ID a80c4f17acd5) |
| Model size in VRAM | 2.6 GB, 100% GPU (from `ollama ps`) |
| Context window | 4096 tokens |
| Prompt | "Explain docker in 3 sentences." |
| Power source | Plugged in (all sessions) |

## Session 1 (2026-10-23): manual runs in chat mode

GPU mode: hybrid (NVIDIA idle at P8, 13 MiB, Disp.A Off before run 1).

| Run | Situation | Prompt tokens | Prompt time | Prompt rate | Output tokens | Output time | Output rate | Total |
|---|---|---|---|---|---|---|---|---|
| 1 | First request after install, Balanced | 33 | 15.743 s | 2.10 tok/s | 100 | 2.520 s | 39.68 tok/s | 18.278 s |
| 2 | Warm, Performance | 32 | 42.68 ms | 749.77 tok/s | 95 | 947.3 ms | 100.28 tok/s | 0.993 s |
| 3 | Warm + KV cache (same chat), Performance | 143 (126 cached, 17 new) | 14.12 ms | 1204.05 tok/s | 65 | 674.5 ms | 96.37 tok/s | 0.699 s |

Note: in run 3, the prompt rate is calculated on the 17 uncached tokens only.

Observations:
1. Run 1 was extremely slow (15.7 s for 33 prompt tokens) although the model was already loaded. See session 3: this was not reproduced and was most likely a one-time first request after installing Ollama.
2. Once warm, prompt processing is much faster than generation (750 vs 100 tok/s): the prompt is processed in parallel, output tokens one at a time.
3. KV cache in chat mode: 126 of 143 prompt tokens were reused from the previous turn.

## Session 2 (2026-10-25): environment problems

- The laptop had been switched to discrete-only GPU mode (MUX). `lspci` showed only the NVIDIA GPU; the only DRM card (card1, vendor 0x10de) drove the internal screen (eDP-1). `prime-select` = on-demand had no effect.
- In this mode the desktop loaded the GPU heavily: gnome-shell used 1.3 to 2.0 GB VRAM, idle utilization 29 to 98%, 74 to 87 C. This persisted after reboot and in both power modes.
- Run A1 (cold, Performance, discrete mode): load 2.944 s, prompt 422.26 tok/s, output 49.93 tok/s, total 5.036 s. Output was half the normal speed because the desktop shared the GPU. Treat as invalid for comparison.
- Fix: switched back to hybrid mode.

## Session 3 (2026-10-26): controlled 2x2 retest (hybrid GPU mode)

Conditions: hybrid mode (desktop on Intel iGPU; NVIDIA idle at 0%, 13 MiB, Disp.A Off), plugged in, only terminal open, Blur my Shell disabled. One-shot command (`ollama run llama3.2:3b --verbose "<prompt>"`), no chat history. Cold = model unloaded with `ollama stop`, GPU idle.

| Run | Mode (power limit) | State | Load time | Prompt rate | Output rate | Total |
|---|---|---|---|---|---|---|
| B1 | Balanced (80 W) | Cold, first load after reboot | 4.598 s | 509.6 tok/s (33 tok) | 106.04 tok/s | 5.607 s |
| B2 | Balanced | Warm (32/33 prompt tokens cached) | 0.001 s | n/a* | 106.00 tok/s | 0.912 s |
| B3 | Balanced | Warm (32/33 cached) | 0.001 s | n/a* | 106.56 tok/s | 0.827 s |
| A1b | Performance (133 W) | Cold | 3.752 s | 778.3 tok/s (33 tok) | 100.17 tok/s | 4.705 s |
| A2 | Performance | Warm (32/33 cached) | 0.001 s | n/a* | 109.41 tok/s | 0.867 s |
| A3 | Performance | Warm (32/33 cached) | 0.001 s | n/a* | 108.39 tok/s | 0.931 s |

*With only 1 uncached token, the reported prompt rate (about 90 to 107 tok/s) measures fixed overhead, not throughput.

## Session 4 (2026-10-30): cache behaviour via the Python client

Hybrid GPU mode, llama3.2:3b, model already loaded. Prompt eval time per run:

| Run | Prompt | Prompt eval |
|---|---|---|
| A1 | docker (first request after load) | 73.3 ms |
| A2 | docker (repeat) | 9.7 ms |
| B1 | git (new) | 11.0 ms |
| B2 | python (new) | 14.9 ms |
| B3 | docker (after git and python) | 14.7 ms |
| B4 | docker (repeat) | 9.8 ms |

Findings:

1. The prompt cache only keeps the last prompt: docker was uncached again after two other prompts (B3).
2. Ollama still reports all 33 prompt tokens on a cache hit, so prompt tok/s computed from a repeated prompt is wrong (about 3,400 tok/s).
3. Only the 6-word question differs between prompts; the chat template in front stays cached, so new vs repeated prompts differ by only about 5 ms.
4. The 73 ms in A1 is first-request overhead after loading, not a cache miss. Warm-up runs remove it.
5. With 33-token prompts, prompt eval time is dominated by fixed overhead. Measuring prompt throughput needs long prompts (hundreds to thousands of tokens).

### Findings

1. **Power mode barely matters for a 3B model:** warm output 106.3 tok/s (Balanced) vs 108.9 tok/s (Performance), about +2.5% despite a much higher power limit (80 W vs 133 W). Small-model token generation is limited by memory bandwidth, not power.
2. **Cold vs warm is mostly load time:** once loaded, even the first request generates at about 100 to 106 tok/s. Most of a cold request's 4.7 to 5.6 s is loading weights (3.8 to 4.6 s).
3. **The load time difference (4.6 s vs 3.8 s) is likely an order effect:** B1 was the first load after reboot (from disk); A1b came later, with the model file probably still in the OS page cache.
4. **The session 1 cold penalty (15.7 s prompt processing) was not reproduced.** It was most likely a one-time first request after installing Ollama, so session 1 run 1 vs run 2 is not a valid warm-up measurement.
5. **Ollama caches identical prompts across separate requests:** even one-shot commands reused 32 of 33 prompt tokens. To measure prompt throughput, each prompt must be unique (e.g. prefix a run ID).
6. **GPU mode matters more than power mode:** discrete-only mode halved the output rate (49.9 tok/s) because the desktop shared the GPU; hybrid mode gives about 100 to 109 tok/s.
7. **The power limit is dynamic** (NVIDIA Dynamic Boost): Balanced showed 80 W and 94 W at different times; Performance 133 W (hybrid) and 140 W (discrete). Record it, but do not infer the mode from it.
8. **Desktop effects affect the iGPU:** Blur my Shell caused heavy typing lag once the desktop moved to the Intel iGPU; disabled for benchmarking.

## Method rules for the script

- Per configuration: 2 warm-up requests (discarded) + 5 measured requests.
- Unique prompt per request (run ID prefix) for throughput tests; a separate experiment for cache effects.
- Record per session: GPU mode, power mode, power limit, idle temperature, open apps.
- Variables: model size (llama3.2:1b, llama3.2:3b, an 8B 4-bit model) and prompt length (short, medium, long).
- Metrics: time to first token, prompt tok/s, output tok/s, total time, VRAM used.

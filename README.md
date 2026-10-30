# LLM Inference Benchmark on a Laptop GPU

Measuring how fast small open LLMs run locally, and which factors actually matter: model size, prompt length, caching, power mode and GPU mode.

**Status:** manual baseline done, automated benchmark script in progress.

## Setup

| Item | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 4070 Laptop GPU, 8 GB VRAM |
| OS | Ubuntu (dual boot), NVIDIA driver 595.99.02, CUDA 13.2 |
| Runtime | Ollama (llama.cpp backend) |
| First model | llama3.2:3b (2.6 GB in VRAM, 100% GPU) |

## Key findings so far (manual runs)

| Condition | Output speed (warm) |
|---|---|
| Balanced power mode (80 W limit) | ~106 tokens/s |
| Performance power mode (133 W limit) | ~109 tokens/s |
| Discrete-only GPU mode (desktop on the same GPU) | ~50 tokens/s |

1. **Power mode barely matters for a 3B model** (+2.5% for 66% more power). Token generation for small models is limited by memory bandwidth, not power.
2. **GPU mode matters a lot:** when the desktop runs on the same GPU (discrete-only / MUX mode), output speed halves. Hybrid mode keeps the NVIDIA GPU free for inference.
3. **A cold start is mostly model loading** (about 3.8 to 4.6 s). Once loaded, even the first request generates at full speed.
4. **Ollama caches identical prompts across requests** (32 of 33 tokens reused), which distorts prompt throughput measurements unless every prompt is unique.
5. **One early outlier was not reproducible** (15.7 s prompt processing on the very first request after installation) and was excluded from conclusions.

Full raw numbers and the reasoning behind each finding: [notes/manual-runs.md](notes/manual-runs.md)

## Method

- Every measured configuration: 2 warm-up requests (discarded), then 5 measured requests.
- Unique prompt per request to avoid unintended KV-cache hits; caching is tested as a separate experiment.
- Conditions recorded per session: GPU mode, power mode, power limit, idle temperature, open applications.
- Only one variable changed at a time.

## Roadmap

- [x] Manual baseline and environment checks
- [ ] Python benchmark script using the Ollama HTTP API (time to first token, prompt tok/s, output tok/s, total time)
- [ ] Compare model sizes: llama3.2:1b, llama3.2:3b, an 8B model in 4-bit
- [ ] Compare prompt lengths: short, medium, long
- [ ] KV-cache experiment: same long prompt with and without cache
- [ ] Charts and final results table
- [ ] Optional: Ollama vs vLLM on the same model

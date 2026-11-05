# Concepts

## What the KV cache is

When a model reads a prompt, it computes a set of numbers for every token,
called keys and values. Ollama keeps these in GPU memory after each request.
If the next prompt starts with the same tokens, the model reuses the stored
values instead of computing them again. This skips part of the prompt reading
(prompt evaluation). Writing the answer (generation) runs at the same speed
either way.

## What I observed in session 4

When I sent the same prompt twice, the second request took almost no time to
read the prompt, but Ollama still reported the full prompt token count.
Dividing the full token count by a near-zero reading time gave a prompt speed
of about 3,400 tokens/s. That number is not real: the model never read those
tokens, it took them from the cache. It is like a typing test that counts a
pasted text as typed.

## Why it matters for this benchmark

Repeating the same prompt measures the cache, not the model. To get honest
numbers, the benchmark:

- runs one warm-up request first, so model loading time is not measured
- sends a unique prompt in every measured run, so the cache cannot help

Results also depend on the machine: the GPU, the power limit, the MUX switch
(whether the GPU also drives the display), and even the operating system. My
laptop dual-boots, and the same test on Windows and Ubuntu would not give
identical numbers. A fixed, automated procedure does not make results
identical across machines, but it makes them comparable.
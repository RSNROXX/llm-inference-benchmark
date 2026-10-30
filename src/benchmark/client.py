"""Client for the Ollama HTTP API.

Sends a single prompt to a locally running Ollama server and returns the
raw response, including Ollama's own timing fields. The benchmark runner
uses this for every measured request.
"""

import requests

from benchmark.metrics import tokens_per_second

OLLAMA_URL = "http://localhost:11434/api/generate"


def generate(model: str, prompt: str) -> dict:
    """Send one non-streaming generation request to Ollama.

    Args:
        model: Ollama model tag, for example "llama3.2:3b".
        prompt: Text to send to the model.

    Returns:
        Ollama's JSON response as a dictionary. Timing fields such as
        eval_count and eval_duration (nanoseconds) are included.

    Raises:
        requests.HTTPError: If Ollama returns an error status.
    """
    response = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    result = generate("llama3.2:3b", "Explain docker in 3 sentences.")

    print("Prompt tokens: ", result["prompt_eval_count"])
    print("Output tokens: ", result["eval_count"])
    print("Load time (s): ", result["load_duration"] / 1_000_000_000)
    print(
        "Output tok/s:  ",
        round(
            tokens_per_second(result["eval_count"],
                              result["eval_duration"]),
            1,
        ),
    )

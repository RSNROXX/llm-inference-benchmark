"""Metric calculations for LLM inference benchmarks.

Turns the raw timing fields returned by Ollama into human-readable
numbers such as tokens per second. Pure functions only, so they can be
unit-tested without a GPU or a running model.
"""

NS_PER_SECOND = 1_000_000_000


def tokens_per_second(token_count: int, duration_ns: int) -> float:
    """Convert a token count and a duration in nanoseconds to tokens/s.

    Args:
        token_count: Number of tokens processed or generated.
        duration_ns: Time taken, in nanoseconds (as reported by Ollama).

    Returns:
        Tokens per second. 0.0 if duration_ns is 0.

    Example:
        >>> tokens_per_second(100, 1_000_000_000)
        100.0
    """
    if duration_ns <= 0:
        return 0.0

    seconds = duration_ns / NS_PER_SECOND
    return token_count / seconds

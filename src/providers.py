"""Compatibility entrypoint for the starter repo's provider module.

The completed lab uses OpenAI for its real-API evaluation and Mock only for
offline logic checks. Live API errors are not silently converted into Mock.
"""

from agent_provider import MockOfflineProvider, OpenAIProvider, get_provider


get_llm_provider = get_provider

__all__ = ["MockOfflineProvider", "OpenAIProvider", "get_llm_provider"]

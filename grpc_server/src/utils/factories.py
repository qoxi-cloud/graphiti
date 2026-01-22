"""Factory classes for creating LLM, Embedder, and Database clients.

Re-exports from server_common for backwards compatibility.
"""

from server_common.factories import (
    DatabaseDriverFactory,
    EmbedderFactory,
    LLMClientFactory,
    create_azure_credential_token_provider,
)

__all__ = [
    'LLMClientFactory',
    'EmbedderFactory',
    'DatabaseDriverFactory',
    'create_azure_credential_token_provider',
]

"""Base servicer with shared Graphiti client."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphiti_core import Graphiti

logger = logging.getLogger(__name__)


class BaseServicer:
    """Base servicer class that holds the Graphiti client reference."""

    def __init__(self, graphiti: 'Graphiti'):
        """Initialize the base servicer with a Graphiti client.

        Args:
            graphiti: The Graphiti client instance to use for all operations.
        """
        self._graphiti = graphiti

    @property
    def graphiti(self) -> 'Graphiti':
        """Get the Graphiti client instance."""
        return self._graphiti

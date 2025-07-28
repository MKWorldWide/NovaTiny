import logging
from typing import Any, Dict

class FusionProtocol:
    """Simple Fusion Protocol activation handler."""

    @staticmethod
    def activate(config: Dict[str, Any]) -> Dict[str, Any]:
        """Activate the Fusion Protocol with the provided configuration."""
        logging.info("🔥 Initiating Fusion Protocol for %s", config.get("codename"))
        logging.debug("Fusion configuration: %s", config)
        return {"fusion_status": "active", **config}

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zyntalic Web Application Launcher
Production-ready startup script with proper configuration
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import WEBAPP_HOST, WEBAPP_PORT, WEBAPP_DEBUG, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Start the Zyntalic web application."""
    try:
        import uvicorn
        
        logger.info("Starting Zyntalic Web Application")
        logger.info(f"Host: {WEBAPP_HOST}")
        logger.info(f"Port: {WEBAPP_PORT}")
        logger.info(f"Debug: {WEBAPP_DEBUG}")
        
        uvicorn.run(
            "webapp.app:app",
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
            reload=WEBAPP_DEBUG,
            log_level=LOG_LEVEL.lower()
        )
    except ImportError:
        logger.error("uvicorn not installed. Install with: pip install uvicorn[standard]")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

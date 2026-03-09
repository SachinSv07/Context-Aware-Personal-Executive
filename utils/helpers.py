"""
Shared utility functions
Used by all modules - keep this file minimal to avoid merge conflicts
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def log_info(message: str) -> None:
    """Log an info message"""
    logger.info(message)


def log_error(message: str, error: Exception = None) -> None:
    """Log an error message"""
    if error:
        logger.error(f"{message}: {str(error)}")
    else:
        logger.error(message)


def format_response(data: Any, source: str = None) -> Dict[str, Any]:
    """
    Format a response from a tool or agent
    
    Args:
        data: The response data
        source: The source of the data (e.g., "email", "pdf", "csv")
    
    Returns:
        Formatted response dictionary
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "data": data
    }


def extract_keywords(text: str) -> List[str]:
    """
    Extract keywords from text (simple implementation)
    TODO: Improve with NLP libraries if needed
    
    Args:
        text: Input text
    
    Returns:
        List of keywords
    """
    # Simple keyword extraction - split and lowercase
    words = text.lower().split()
    # Remove common stop words (basic list)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple similarity between two texts
    TODO: Replace with proper similarity metric if needed
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Similarity score (0.0 to 1.0)
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

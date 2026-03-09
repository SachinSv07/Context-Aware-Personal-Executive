"""
Base class for all data search tools
Developer 1: Use this as a template for implementing specific tools
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from utils.helpers import log_info, format_response


class BaseTool(ABC):
    """
    Abstract base class for all search tools
    Each tool should inherit from this class
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize the tool
        
        Args:
            name: Tool name (e.g., "search_email")
            description: Tool description for the LLM agent
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search the data source
        
        Args:
            query: User's search query
        
        Returns:
            List of search results
        """
        pass
    
    def get_tool_spec(self) -> Dict[str, Any]:
        """
        Get the tool specification for OpenAI function calling
        
        Returns:
            Tool specification dictionary
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    def execute(self, query: str) -> Dict[str, Any]:
        """
        Execute the search and format the response
        
        Args:
            query: User's search query
        
        Returns:
            Formatted response
        """
        log_info(f"Executing {self.name} with query: {query}")
        results = self.search(query)
        return format_response(results, source=self.name)

"""
Tool Registry - manages available tools for the agent
Developer 2: This connects your agent to Developer 1's tools
"""

from typing import Dict, Callable, List, Any
from tools.gmail_tool import search_gmail, GMAIL_TOOL_SPEC
from tools.drive_tool import search_drive, DRIVE_TOOL_SPEC
from tools.calendar_tool import search_calendar, CALENDAR_TOOL_SPEC
from tools.pdf_tool import search_pdf, PDF_TOOL_SPEC
from tools.csv_tool import search_csv, CSV_TOOL_SPEC
from utils.helpers import log_info


class ToolRegistry:
    """
    Registry of available tools for the agent
    Maps tool names to their implementations and specifications
    """
    
    def __init__(self):
        """Initialize the tool registry"""
        self.tools: Dict[str, Callable] = {}
        self.tool_specs: List[Dict[str, Any]] = []
        self._register_tools()
    
    def _register_tools(self):
        """
        Register all available tools
        Developer 2: Add new tools here as Developer 1 implements them
        """
        # Register Gmail search tool
        self.tools["search_gmail"] = search_gmail
        self.tool_specs.append(GMAIL_TOOL_SPEC)
        
            # Register Google Drive search tool
            self.tools["search_drive"] = search_drive
            self.tool_specs.append(DRIVE_TOOL_SPEC)
        
            # Register Google Calendar search tool
            self.tools["search_calendar"] = search_calendar
            self.tool_specs.append(CALENDAR_TOOL_SPEC)
        
        # Register PDF search tool
        self.tools["search_pdf"] = search_pdf
        self.tool_specs.append(PDF_TOOL_SPEC)
        
        # Register CSV search tool
        self.tools["search_csv"] = search_csv
        self.tool_specs.append(CSV_TOOL_SPEC)
        
        log_info(f"Registered {len(self.tools)} tools")
    
    def get_tool(self, tool_name: str) -> Callable:
        """
        Get a tool by name
        
        Args:
            tool_name: Name of the tool
        
        Returns:
            Tool function
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        return self.tools[tool_name]
    
    def get_tool_specs(self) -> List[Dict[str, Any]]:
        """
        Get all tool specifications for OpenAI function calling
        
        Returns:
            List of tool specifications
        """
        return self.tool_specs
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool with the given arguments
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool arguments
        
        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)
        log_info(f"Executing tool: {tool_name} with args: {kwargs}")
        return tool(**kwargs)
    
    def list_tools(self) -> List[str]:
        """
        List all available tool names
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())


# Create a global instance
tool_registry = ToolRegistry()


if __name__ == "__main__":
    # Test the tool registry
    registry = ToolRegistry()
    print("Available tools:", registry.list_tools())
    
    # Test executing a tool
    result = registry.execute_tool("search_gmail", query="meeting")
    print(f"Tool execution result: {result}")


"""
LLM Agent - Core AI logic
Powered by Google Gemini with function calling (google-genai SDK)
"""

import json
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL, AGENT_TEMPERATURE, MAX_AGENT_ITERATIONS
from agent.tool_registry import ToolRegistry
from utils.helpers import log_info, log_error


class ContextAwareAgent:
    """
    AI Agent that uses Google Gemini function calling to select and execute tools.
    """

    SYSTEM_PROMPT = (
        "You are a helpful AI assistant that searches across multiple personal data sources "
        "(emails, Google Drive, Google Calendar, PDFs, and CSV notes) to answer questions. "
        "Always use the available tools to find relevant information and cite your sources."
    )

    def __init__(self):
        """Initialize the Gemini-powered agent."""
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.tool_registry = ToolRegistry()
        self.temperature = AGENT_TEMPERATURE
        self.conversation_history: List[Dict[str, str]] = []
        self._gemini_tools = self._build_gemini_tools()
        log_info(f"Initialized ContextAwareAgent with model: {GEMINI_MODEL}")

    # ------------------------------------------------------------------
    # Tool conversion helpers
    # ------------------------------------------------------------------

    def _build_gemini_tools(self):
        """
        Convert OpenAI-style tool specs (from the registry) into Gemini
        FunctionDeclaration objects using the new google-genai SDK.
        """
        openai_specs = self.tool_registry.get_tool_specs()
        declarations = []

        for spec in openai_specs:
            fn = spec["function"]
            params = fn.get("parameters", {})
            properties = params.get("properties", {})
            required = params.get("required", [])

            gemini_props = {}
            for prop_name, prop_info in properties.items():
                gemini_props[prop_name] = types.Schema(
                    type="STRING",
                    description=prop_info.get("description", ""),
                )

            declarations.append(
                types.FunctionDeclaration(
                    name=fn["name"],
                    description=fn.get("description", ""),
                    parameters=types.Schema(
                        type="OBJECT",
                        properties=gemini_props,
                        required=required,
                    ),
                )
            )

        return types.Tool(function_declarations=declarations)

    # ------------------------------------------------------------------
    # Query processing
    # ------------------------------------------------------------------

    def process_query(self, user_query: str) -> str:
        """
        Process a user query with Gemini function calling.

        Args:
            user_query: The user's question/query

        Returns:
            Agent's response string
        """
        log_info(f"Processing query: {user_query}")

        try:
            config = types.GenerateContentConfig(
                tools=[self._gemini_tools],
                system_instruction=self.SYSTEM_PROMPT,
                temperature=self.temperature,
            )

            chat = self.client.chats.create(model=GEMINI_MODEL, config=config)
            response = chat.send_message(user_query)

            # Agentic loop: keep handling function calls until a text answer arrives
            for _ in range(MAX_AGENT_ITERATIONS):
                function_calls = [
                    part.function_call
                    for part in response.candidates[0].content.parts
                    if part.function_call and part.function_call.name
                ]

                if not function_calls:
                    break  # Model returned a text answer

                # Execute every requested tool and send responses back
                tool_response_parts = []
                for fc in function_calls:
                    tool_name = fc.name
                    tool_args = dict(fc.args)
                    log_info(f"Agent calling tool: {tool_name} with args: {tool_args}")

                    tool_result = self.tool_registry.execute_tool(tool_name, **tool_args)

                    tool_response_parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=tool_name,
                                response={"result": json.dumps(tool_result, default=str)},
                            )
                        )
                    )

                response = chat.send_message(tool_response_parts)

            answer = response.text
            log_info("Agent response generated successfully")
            return answer

        except Exception as e:
            log_error("Error processing query", e)
            return f"I apologize, but I encountered an error processing your query: {str(e)}"
    
    def process_query_with_history(self, user_query: str) -> str:
        """
        Process query with conversation history (for multi-turn conversations)
        
        Args:
            user_query: The user's question/query
        
        Returns:
            Agent's response
        
        Developer 2: Implement this for maintaining conversation context
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_query
        })
        
        response = self.process_query(user_query)
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        log_info("Conversation history reset")
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return self.tool_registry.list_tools()


# Example alternative implementation using a simple rule-based approach
class SimpleAgent:
    """
    Simplified agent without OpenAI (for testing without API key)
    Developer 2: Use this for quick testing
    """
    
    def __init__(self):
        self.tool_registry = ToolRegistry()
    
    def process_query(self, user_query: str) -> str:
        """Simple keyword-based tool selection"""
        query_lower = user_query.lower()
        results = []
        
        # Simple keyword matching
        if any(word in query_lower for word in ['email', 'message', 'mail', 'sent', 'received']):
            email_results = self.tool_registry.execute_tool("search_email", query=user_query)
            results.append(f"Email search results: {email_results}")
        
        if any(word in query_lower for word in ['document', 'pdf', 'report', 'paper']):
            pdf_results = self.tool_registry.execute_tool("search_pdf", query=user_query)
            results.append(f"PDF search results: {pdf_results}")
        
        if any(word in query_lower for word in ['note', 'csv', 'data', 'record']):
            csv_results = self.tool_registry.execute_tool("search_csv", query=user_query)
            results.append(f"CSV search results: {csv_results}")
        
        # If no specific data source matched, search all
        if not results:
            email_results = self.tool_registry.execute_tool("search_email", query=user_query)
            pdf_results = self.tool_registry.execute_tool("search_pdf", query=user_query)
            csv_results = self.tool_registry.execute_tool("search_csv", query=user_query)
            
            return f"""
            I searched across all data sources for '{user_query}':
            
            Emails: {len(email_results)} results found
            PDFs: {len(pdf_results)} results found
            CSV Notes: {len(csv_results)} results found
            
            Combined results: {email_results + pdf_results + csv_results}
            """
        
        return "\n\n".join(results)


if __name__ == "__main__":
    # Test the agent
    agent = ContextAwareAgent()
    
    # Test query
    test_query = "Find emails about the project meeting"
    response = agent.process_query(test_query)
    print(f"Query: {test_query}")
    print(f"Response: {response}")

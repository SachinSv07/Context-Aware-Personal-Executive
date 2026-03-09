"""
LLM Agent - Core AI logic
Developer 2: Implement the AI agent here using OpenAI function calling
"""

import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, AGENT_TEMPERATURE, MAX_AGENT_ITERATIONS
from agent.tool_registry import ToolRegistry
from utils.helpers import log_info, log_error


class ContextAwareAgent:
    """
    AI Agent that uses OpenAI function calling to select and execute tools
    
    Developer 2 TODO:
        1. Initialize OpenAI client
        2. Implement query processing logic
        3. Use OpenAI function calling to select tools
        4. Execute selected tools
        5. Synthesize final answer from tool results
        6. Handle multi-step reasoning if needed
    """
    
    def __init__(self):
        """Initialize the agent"""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.temperature = AGENT_TEMPERATURE
        self.tool_registry = ToolRegistry()
        self.conversation_history: List[Dict[str, str]] = []
        
        log_info(f"Initialized ContextAwareAgent with model: {self.model}")
    
    def process_query(self, user_query: str) -> str:
        """
        Process a user query and return a response
        
        Args:
            user_query: The user's question/query
        
        Returns:
            Agent's response
        
        Developer 2: This is the main method to implement
        """
        log_info(f"Processing query: {user_query}")
        
        try:
            # Add user message to conversation
            messages = [
                {
                    "role": "system",
                    "content": """You are a helpful AI assistant that can search across multiple data sources 
                    (emails, PDFs, and CSV notes) to answer user questions. Use the available tools to find 
                    relevant information and provide comprehensive answers. Always cite your sources."""
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ]
            
            # Get tool specifications
            tools = self.tool_registry.get_tool_specs()
            
            # Initial API call with function calling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=self.temperature
            )
            
            # Process the response
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # If the model wants to call tools
            if tool_calls:
                # Execute each tool call
                messages.append(response_message)
                
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    log_info(f"Agent calling tool: {tool_name} with args: {tool_args}")
                    
                    # Execute the tool
                    tool_result = self.tool_registry.execute_tool(tool_name, **tool_args)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps(tool_result)
                    })
                
                # Get final response after tool execution
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature
                )
                
                answer = final_response.choices[0].message.content
            else:
                # No tools needed, use direct response
                answer = response_message.content
            
            log_info(f"Agent response generated successfully")
            return answer
        
        except Exception as e:
            log_error(f"Error processing query", e)
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

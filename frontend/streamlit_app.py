"""
Streamlit Chat Interface
Developer 3: Build the chat UI here

To run: streamlit run frontend/streamlit_app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.llm_agent import ContextAwareAgent
from utils.helpers import log_info


def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'agent' not in st.session_state:
        st.session_state.agent = ContextAwareAgent()


def main():
    """
    Main Streamlit application
    
    Developer 3 TODO:
        1. Create a clean chat interface
        2. Display conversation history
        3. Add input box for user queries
        4. Show loading spinner while processing
        5. Format agent responses nicely
        6. Add sidebar with settings/info
        7. Add error handling
        8. (Optional) Add file upload functionality
    """
    
    # Page configuration
    st.set_page_config(
        page_title="Context-Aware Personal Executive",
        page_icon="🤖",
        layout="wide"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("🤖 Context-Aware Personal Executive")
    st.markdown("Ask questions about your emails, documents, and notes!")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        st.markdown("### Available Data Sources")
        st.markdown("- 📧 Emails")
        st.markdown("- 📄 PDF Documents")
        st.markdown("- 📊 CSV Notes")
        
        st.markdown("---")
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            st.session_state.agent.reset_conversation()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This AI assistant searches across your personal data sources 
        to answer questions and retrieve information.
        
        **How it works:**
        1. Type your question
        2. AI agent selects relevant tools
        3. Tools search your data
        4. AI synthesizes the answer
        """)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your emails, documents, or notes..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.agent.process_query(prompt)
                    st.markdown(response)
                    
                    # Add assistant response to chat
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_message = f"⚠️ Error: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: gray;'>Built for Hackathon | "
        "Powered by OpenAI & Python</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

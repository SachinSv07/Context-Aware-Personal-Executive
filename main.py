"""
Main entry point for Context-Aware Personal Executive
Run this file to start the application
"""

import sys
import argparse
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from agent.llm_agent import ContextAwareAgent, SimpleAgent
from utils.helpers import log_info


def run_cli():
    """
    Run the CLI version (for quick testing)
    """
    print("=" * 60)
    print("Context-Aware Personal Executive - CLI Mode")
    print("=" * 60)
    print("\nType 'quit' or 'exit' to stop\n")
    
    # Use SimpleAgent for testing without API key
    # Switch to ContextAwareAgent when you have OpenAI API key
    try:
        agent = ContextAwareAgent()
        print("✓ Using OpenAI-powered agent")
    except Exception as e:
        print(f"⚠ OpenAI not available, using simple agent: {e}")
        agent = SimpleAgent()
    
    while True:
        try:
            user_input = input("\n🤔 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\n🤖 Assistant: ", end="", flush=True)
            response = agent.process_query(user_input)
            print(response)
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def run_streamlit():
    """
    Run the Streamlit frontend
    """
    import subprocess
    
    streamlit_app = PROJECT_ROOT / "frontend" / "streamlit_app.py"
    
    print("=" * 60)
    print("Starting Streamlit Frontend...")
    print("=" * 60)
    print(f"\nAccess the app at: http://localhost:8501")
    print("Press Ctrl+C to stop\n")
    
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(streamlit_app)])


def run_flask():
    """
    Run the Flask frontend
    """
    from frontend.flask_app import app, FLASK_PORT, FLASK_DEBUG
    
    print("=" * 60)
    print("Starting Flask Frontend...")
    print("=" * 60)
    print(f"\nAccess the app at: http://localhost:{FLASK_PORT}")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)


def run_tests():
    """
    Run quick tests of all components
    """
    print("=" * 60)
    print("Running Component Tests")
    print("=" * 60)
    
    # Test tools
    print("\n1. Testing Data Tools...")
    from tools import search_email, search_pdf, search_csv
    
    print("   - Email search:", end=" ")
    email_results = search_email("meeting")
    print(f"✓ Found {len(email_results)} results")
    
    print("   - PDF search:", end=" ")
    pdf_results = search_pdf("project")
    print(f"✓ Found {len(pdf_results)} results")
    
    print("   - CSV search:", end=" ")
    csv_results = search_csv("hackathon")
    print(f"✓ Found {len(csv_results)} results")
    
    # Test agent
    print("\n2. Testing Agent...")
    try:
        agent = ContextAwareAgent()
        print("   ✓ ContextAwareAgent initialized")
    except Exception as e:
        print(f"   ⚠ ContextAwareAgent failed: {e}")
        print("   ✓ Using SimpleAgent instead")
        agent = SimpleAgent()
    
    print("\n3. Test Query: 'Find emails about meetings'")
    response = agent.process_query("Find emails about meetings")
    print(f"   Response preview: {response[:200]}...")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)


def main():
    """
    Main entry point with argument parsing
    """
    parser = argparse.ArgumentParser(
        description="Context-Aware Personal Executive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run CLI mode
  python main.py --streamlit        # Run Streamlit UI
  python main.py --flask            # Run Flask UI
  python main.py --test             # Run tests
        """
    )
    
    parser.add_argument(
        '--streamlit',
        action='store_true',
        help='Run Streamlit frontend'
    )
    
    parser.add_argument(
        '--flask',
        action='store_true',
        help='Run Flask frontend'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run component tests'
    )
    
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Run in CLI mode (default)'
    )
    
    args = parser.parse_args()
    
    # Check environment
    import os
    if not os.getenv('OPENAI_API_KEY'):
        print("\n⚠️  WARNING: OPENAI_API_KEY not set in environment")
        print("   The agent will use a simple fallback mode")
        print("   Set your API key: export OPENAI_API_KEY='your-key-here'\n")
    
    # Execute based on arguments
    if args.streamlit:
        run_streamlit()
    elif args.flask:
        run_flask()
    elif args.test:
        run_tests()
    else:
        # Default to CLI mode
        run_cli()


if __name__ == "__main__":
    main()

"""
Command-line interface for GROMACS Copilot
"""

import os
import sys
import argparse
import logging

from gromacs_copilot.core.md_agent import MDLLMAgent
from gromacs_copilot.utils.terminal import Colors, print_message
from gromacs_copilot.utils.logging_utils import setup_logging
from gromacs_copilot.core.enums import MessageType
from gromacs_copilot.config import DEFAULT_WORKSPACE, DEFAULT_MODEL, DEFAULT_OPENAI_URL


def parse_arguments():
    """
    Parse command-line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="GROMACS Copilot")
    parser.add_argument("--api-key", help="API key for LLM service")
    parser.add_argument("--url", 
                      help=(
                          "The url of the LLM service, "
                          "\ndeepseek: https://api.deepseek.com/chat/completions"
                          "\nopenai: https://api.openai.com/v1/chat/completions"
                      ), 
                      default=DEFAULT_OPENAI_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model to use for LLM")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE, help="Workspace directory")
    parser.add_argument("--prompt", help="Starting prompt for the LLM")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--log-file", default="md_agent.log", help="Log file path")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Logging level")
    
    return parser.parse_args()


def main():
    """
    Main entry point for the CLI
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(args.log_file, level=log_level)
    
    # Disable colors if requested or if not in a terminal
    if args.no_color or not sys.stdout.isatty():
        Colors.disable_colors()
    
    # Display splash screen
    print_message("", style="divider")
    print_message("GROMACS Copilot", MessageType.TITLE, style="box")
    print_message("A molecular dynamics simulation assistant powered by AI, created by the ChatMol Team.", MessageType.INFO)
    print_message("", style="divider")
    
    try:
        # Check for API key
        if args.url == "https://api.openai.com/v1/chat/completions":
            api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
        elif args.url == "https://api.deepseek.com/chat/completions":
            api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY")
        else:
            api_key = args.api_key

        if not api_key:
            print_message(
                "API key not found. Please provide an API key using --api-key or set the "
                "OPENAI_API_KEY or DEEPSEEK_API_KEY environment variable.", 
                MessageType.ERROR
            )
            sys.exit(1)
        
        # Create and run MD LLM agent
        print_message(f"Initializing with model: {args.model}", MessageType.INFO)
        print_message(f"Using workspace: {args.workspace}", MessageType.INFO)
        
        agent = MDLLMAgent(
            api_key=api_key, 
            model=args.model, 
            workspace=args.workspace, 
            url=args.url
        )
        agent.run(starting_prompt=args.prompt)
        
    except KeyboardInterrupt:
        print_message("\nExiting the MD agent. Thank you for using GROMACS Copilot!", 
                     MessageType.SUCCESS, style="box")
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error running MD LLM agent: {error_msg}")
        print_message(f"Error running MD LLM agent: {error_msg}", 
                     MessageType.ERROR, style="box")


if __name__ == "__main__":
    main()
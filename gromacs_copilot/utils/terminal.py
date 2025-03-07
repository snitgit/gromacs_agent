"""
Terminal output formatting utilities for GROMACS Copilot
"""

import sys
import shutil
from typing import Optional

from gromacs_copilot.core.enums import MessageType

class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Bright variants
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    @classmethod
    def disable_colors(cls):
        """Disable all colors by setting them to empty strings"""
        for attr in dir(cls):
            if not attr.startswith('__') and not callable(getattr(cls, attr)):
                setattr(cls, attr, '')


def should_use_colors() -> bool:
    """
    Determine if colors should be used in terminal output
    
    Returns:
        bool: True if colors should be used, False otherwise
    """
    return sys.stdout.isatty()


def print_message(message: str, msg_type: MessageType = MessageType.INFO, 
                  style: Optional[str] = None, width: Optional[int] = None):
    """
    Print a formatted message to the console
    
    Args:
        message: The message to print
        msg_type: Type of message (info, success, warning, error, etc.)
        style: Optional additional styling (box, divider)
        width: Width of the message box (defaults to terminal width)
    """
    # Get terminal width if not specified
    if not width:
        try:
            width = shutil.get_terminal_size().columns
        except:
            width = 80
    
    # Configure colors and prefixes based on message type
    if msg_type == MessageType.INFO:
        color = Colors.CYAN
        prefix = "ℹ️  INFO    │ "
    elif msg_type == MessageType.SUCCESS:
        color = Colors.GREEN
        prefix = "✓  SUCCESS │ "
    elif msg_type == MessageType.WARNING:
        color = Colors.YELLOW
        prefix = "⚠️  WARNING │ "
    elif msg_type == MessageType.ERROR:
        color = Colors.RED
        prefix = "✗  ERROR   │ "
    elif msg_type == MessageType.TITLE:
        color = Colors.BRIGHT_BLUE + Colors.BOLD
        prefix = "🧪 "
    elif msg_type == MessageType.SYSTEM:
        color = Colors.BRIGHT_MAGENTA
        prefix = "🤖 SYSTEM  │ "
    elif msg_type == MessageType.USER:
        color = Colors.BRIGHT_CYAN
        prefix = "👤 USER    │ "
    elif msg_type == MessageType.COMMAND:
        color = Colors.BRIGHT_BLACK
        prefix = "$ "
    elif msg_type == MessageType.TOOL:
        color = Colors.BRIGHT_GREEN
        prefix = "🔧 TOOL    │ "
    elif msg_type == MessageType.FINAL:
        color = Colors.BRIGHT_GREEN + Colors.BOLD
        prefix = "🏁 FINAL   │ "
    else:
        color = ""
        prefix = ""
    
    # Apply styling
    if style == "box":
        box_width = width - 4  # Account for side margins
        print(f"{color}┌{'─' * box_width}┐{Colors.RESET}")
        
        # Split message into lines that fit within the box
        lines = []
        curr_line = ""
        
        for word in message.split():
            if len(curr_line) + len(word) + 1 <= box_width - 4:  # -4 for margins
                curr_line += word + " "
            else:
                lines.append(curr_line)
                curr_line = word + " "
        if curr_line:
            lines.append(curr_line)
        
        # Print each line within the box
        for line in lines:
            padding = box_width - len(line) - 2
            print(f"{color}│ {line}{' ' * padding} │{Colors.RESET}")
        
        print(f"{color}└{'─' * box_width}┘{Colors.RESET}")
    
    elif style == "divider":
        print(f"{color}{'═' * width}{Colors.RESET}")
        print(f"{color}{prefix}{message}{Colors.RESET}")
        print(f"{color}{'═' * width}{Colors.RESET}")
    
    else:
        # Basic formatting with prefix
        print(f"{color}{prefix}{message}{Colors.RESET}")


def prompt_user(message: str, default: Optional[str] = None, 
                choices: Optional[list] = None) -> str:
    """
    Prompt the user for input with optional default value and choices
    
    Args:
        message: The message to display to the user
        default: Optional default value if user hits enter
        choices: Optional list of valid choices
        
    Returns:
        str: The user's response
    """
    # Format message with default value if provided
    if default is not None:
        prompt = f"{Colors.BRIGHT_CYAN}{message} [{default}]: {Colors.RESET}"
    else:
        prompt = f"{Colors.BRIGHT_CYAN}{message}: {Colors.RESET}"
    
    # Print choices if provided
    if choices:
        for i, choice in enumerate(choices, 1):
            print(f"{Colors.BRIGHT_CYAN}  {i}. {choice}{Colors.RESET}")
        
        while True:
            response = input(prompt)
            
            # Use default if empty response and default provided
            if not response and default is not None:
                return default
            
            # Try to interpret as a choice number
            try:
                choice_idx = int(response) - 1
                if 0 <= choice_idx < len(choices):
                    return choices[choice_idx]
                else:
                    print(f"{Colors.YELLOW}Please enter a number between 1 and {len(choices)}{Colors.RESET}")
            except ValueError:
                # If response matches a choice directly, return it
                if response in choices:
                    return response
                print(f"{Colors.YELLOW}Please enter a valid choice{Colors.RESET}")
    else:
        # Simple prompt without choices
        response = input(prompt)
        
        # Use default if empty response and default provided
        if not response and default is not None:
            return default
        
        return response
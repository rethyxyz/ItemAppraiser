import os
import sys
import subprocess
import argparse
import platform
import rethyxyz.rethyxyz

# Global variable to hold the total size
total_size = 0

class AsciiArt:
    BRANCH = '├── '
    LAST_BRANCH = '└── '
    VERTICAL = '│   '
    SPACE = '    '

class Colors:
    WHITE = '\033[97m'  # For smaller files/directories
    GREEN = '\033[92m'  # For medium files/directories
    YELLOW = '\033[93m' # For large files/directories
    RED = '\033[91m'    # For very large files/directories
    BLUE = '\033[94m'   # Additional color, could be used for default text or directories
    RESET = '\033[0m'   # Reset to default

if platform.system() == 'Windows':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        Colors.WHITE = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.RED = ''
        Colors.RESET = ''

def is_double_clicked():
    if platform.system() == "Windows":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        return kernel32.GetConsoleProcessList(ctypes.byref(ctypes.c_ulong()), 1) == 1
    else:
        return False

def relaunch_in_terminal():
    if platform.system() == "Windows":
        script_path = ' '.join(['"' + arg + '"' if ' ' in arg else arg for arg in sys.argv])
        cmd_command = f'start cmd /k python {script_path} && echo. && pause'
        subprocess.run(cmd_command, shell=True)
        sys.exit(0)
    else:
        print("This feature is not supported on non-Windows platforms.")
        sys.exit(1)

def get_size(start_path):
    """Return the size of a file or the total size of the contents of a directory."""
    if os.path.isfile(start_path):
        return os.path.getsize(start_path)
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def size_to_string(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def size_to_color(size):
    if size <= 10 * 1024**2:  # Up to 10MB
        return Colors.WHITE
    elif size <= 100 * 1024**2:  # Greater than 10MB and up to 100MB
        return Colors.GREEN
    elif size <= 1024**3:  # Greater than 100MB and up to 1GB
        return Colors.YELLOW
    else:  # Greater than 1GB
        return Colors.RED

def safe_print(content):
    """Safely print content, replacing non-UTF-8 characters if necessary."""
    try:
        print(content)
    except UnicodeEncodeError:
        encoded_content = content.encode('utf-8', 'replace').decode('utf-8', 'replace')
        print(encoded_content + " (Note: Filename contains characters that could not be encoded in UTF-8.)")

def list_contents(path, prefix=''):
    global total_size
    try:
        items = os.listdir(path)
    except FileNotFoundError:
        safe_print(f"{Colors.RED}Error: {path} does not exist.{Colors.RESET}")
        return
    except PermissionError:
        safe_print(f"{prefix}{Colors.RED}PermissionError accessing {path}{Colors.RESET}")
        return

    items.sort(key=lambda x: x.lower())  # Sort items for consistent order
    for i, item in enumerate(items):
        full_path = os.path.join(path, item)
        is_last = i == (len(items) - 1)

        try:
            if os.path.isdir(full_path):
                os.listdir(full_path)
            item_size = get_size(full_path)
            total_size += item_size
        except FileNotFoundError:
            safe_print(f"{prefix}{Colors.RED}Error: {full_path} was not found.{Colors.RESET}")
            continue
        except PermissionError:
            safe_print(f"{prefix}{Colors.RED}PermissionError: {item}{Colors.RESET}")
            continue

        size_str = size_to_string(item_size)
        color = size_to_color(item_size)
        item_color = Colors.GREEN if os.path.isfile(full_path) else Colors.BLUE
        
        # Determine the correct prefix for the tree structure
        tree_prefix = AsciiArt.LAST_BRANCH if is_last else AsciiArt.BRANCH
        # Apply color to the tree structure and reset before printing the item name
        safe_print(f"{prefix}{color}{tree_prefix}{Colors.RESET}{item_color}{item}{Colors.RESET} ({size_str})")
        
        # Update the prefix for the next level, if not the last item use vertical bar
        next_prefix = prefix + (AsciiArt.SPACE if is_last else AsciiArt.VERTICAL)
        if os.path.isdir(full_path):
            # Recursive call to list contents of a directory
            list_contents(full_path, next_prefix)

def main():
    global total_size
    parser = argparse.ArgumentParser(description="ItemAppraiser: Assess the size of your items (files and directories).")
    
    # Add the --no-motd (-m) flag to disable the intro message
    parser.add_argument('--no-motd', '-m', action='store_true', help="Disable the message of the day (intro message).")
    parser.add_argument('paths', nargs='*', default=['.'], help="Specify the paths to check. Defaults to the current location.")
    
    args = parser.parse_args()

    # Check for double click to relaunch in terminal on Windows
    if is_double_clicked():
        relaunch_in_terminal()

    # Show intro message if --no-motd (-m) flag is not used
    if not args.no_motd:
        rethyxyz.rethyxyz.show_intro("ItemAppraiser")

    # Exit if no arguments are provided
    if len(sys.argv) == 1:
        print("Error: No arguments provided.")
        parser.print_help()
        sys.exit(1)

    if not args.paths:
        print("Error: No paths specified.")
        sys.exit(1)

    for path in args.paths:
        safe_print(f"{Colors.BLUE}Appraising: {path}{Colors.RESET}")
        list_contents(path)

    # Display the total size at the end
    safe_print(f"\nTotal size: {size_to_string(total_size)}")

if __name__ == "__main__":
    main()

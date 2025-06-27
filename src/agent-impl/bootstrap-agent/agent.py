#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path
from textwrap import dedent
from typing import List, Dict, Any, Optional
# 
from openai import OpenAI
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
# 
from pydantic import BaseModel
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.style import Style
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style as PromptStyle
import time

# Initialize Rich console and prompt session
console = Console()
prompt_session = PromptSession(
    style=PromptStyle.from_dict({
        'prompt': '#0066ff bold',  # Bright blue prompt
        'completion-menu.completion': 'bg:#1e3a8a fg:#ffffff',
        'completion-menu.completion.current': 'bg:#3b82f6 fg:#ffffff bold',
    })
)

# --------------------------------------------------------------------------------
# 1. Configure OpenAI client and load environment variables
# --------------------------------------------------------------------------------
load_dotenv()  # Load environment variables from .env file

# Configure OpenAI client for OpenRouter
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), 
    base_url="https://openrouter.ai/api/v1"
)

# Model configuration
# MODEL_NAME = "qwen/qwen-2.5-coder-32b-instruct"
# MODEL_NAME = "mistralai/devstral-small-2505"
MODEL_NAME = "google/gemini-2.5-pro-preview"

# --------------------------------------------------------------------------------
# 2. Define our schema using Pydantic for type safety
# --------------------------------------------------------------------------------
class FileToCreate(BaseModel):
    path: str
    content: str

class FileToEdit(BaseModel):
    path: str
    original_snippet: str
    new_snippet: str

# Remove AssistantResponse as we're using function calling now

# --------------------------------------------------------------------------------
# 2.1. Define Function Calling Tools
# --------------------------------------------------------------------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a single file from the filesystem",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to read (relative or absolute)",
                    }
                },
                "required": ["file_path"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_multiple_files",
            "description": "Read the content of multiple files from the filesystem",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of file paths to read (relative or absolute)",
                    }
                },
                "required": ["file_paths"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a new file or overwrite an existing file with the provided content",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path where the file should be created",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file",
                    }
                },
                "required": ["file_path", "content"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_multiple_files",
            "description": "Create multiple files at once",
            "parameters": {
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["path", "content"]
                        },
                        "description": "Array of files to create with their paths and content",
                    }
                },
                "required": ["files"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit an existing file by replacing a specific snippet with new content",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to edit",
                    },
                    "original_snippet": {
                        "type": "string",
                        "description": "The exact text snippet to find and replace",
                    },
                    "new_snippet": {
                        "type": "string",
                        "description": "The new text to replace the original snippet with",
                    }
                },
                "required": ["file_path", "original_snippet", "new_snippet"]
            },
        }
    }
]

# --------------------------------------------------------------------------------
# 3. system prompt
# --------------------------------------------------------------------------------
system_PROMPT = dedent("""\
    You are an elite software engineer called DeepSeek Engineer with decades of experience across all programming domains.
    Your expertise spans system design, algorithms, testing, and best practices.
    You provide thoughtful, well-structured solutions while explaining your reasoning.

    Core capabilities:
    1. Code Analysis & Discussion
       - Analyze code with expert-level insight
       - Explain complex concepts clearly
       - Suggest optimizations and best practices
       - Debug issues with precision

    2. File Operations (via function calls):
       - read_file: Read a single file's content
       - read_multiple_files: Read multiple files at once
       - create_file: Create or overwrite a single file
       - create_multiple_files: Create multiple files at once
       - edit_file: Make precise edits to existing files using snippet replacement

    Guidelines:
    1. Provide natural, conversational responses explaining your reasoning
    2. Use function calls when you need to read or modify files
    3. For file operations:
       - Always read files first before editing them to understand the context
       - Use precise snippet matching for edits
       - Explain what changes you're making and why
       - Consider the impact of changes on the overall codebase
    4. Follow language-specific best practices
    5. Suggest tests or validation steps when appropriate
    6. Be thorough in your analysis and recommendations

    IMPORTANT: In your thinking process, if you realize that something requires a tool call, cut your thinking short and proceed directly to the tool call. Don't overthink - act efficiently when file operations are needed.

    Remember: You're a senior engineer - be thoughtful, precise, and explain your reasoning clearly.
""")

# --------------------------------------------------------------------------------
# 4. Helper functions 
# --------------------------------------------------------------------------------

def read_local_file(file_path: str) -> str:
    """Return the text content of a local file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def create_file(path: str, content: str):
    """Create (or overwrite) a file at 'path' with the given 'content'."""
    file_path = Path(path)
    
    # Security checks
    if any(part.startswith('~') for part in file_path.parts):
        raise ValueError("Home directory references not allowed")
    normalized_path = normalize_path(str(file_path))
    
    # Validate reasonable file size for operations
    if len(content) > 5_000_000:  # 5MB limit
        raise ValueError("File content exceeds 5MB size limit")
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    console.print(f"[bold blue]✓[/bold blue] Created/updated file at '[bright_cyan]{file_path}[/bright_cyan]'")

def show_diff_table(files_to_edit: List[FileToEdit]) -> None:
    if not files_to_edit:
        return
    
    table = Table(title="📝 Proposed Edits", show_header=True, header_style="bold bright_blue", show_lines=True, border_style="blue")
    table.add_column("File Path", style="bright_cyan", no_wrap=True)
    table.add_column("Original", style="red dim")
    table.add_column("New", style="bright_green")

    for edit in files_to_edit:
        table.add_row(edit.path, edit.original_snippet, edit.new_snippet)
    
    console.print(table)

def apply_diff_edit(path: str, original_snippet: str, new_snippet: str) -> tuple[bool, str]:
    """Reads the file at 'path', replaces the first occurrence of 'original_snippet' with 'new_snippet', then overwrites.
    Returns (success: bool, message: str)"""
    try:
        content = read_local_file(path)
        
        # Check for None content
        if content is None:
            error_msg = f"File content is None for '{path}'"
            console.print(f"[bold red]✗[/bold red] {error_msg}")
            return False, error_msg
        
        # Verify we're replacing the exact intended occurrence
        occurrences = content.count(original_snippet)
        if occurrences == 0:
            error_msg = "Original snippet not found"
            console.print(f"[bold yellow]⚠[/bold yellow] {error_msg} in '[bright_cyan]{path}[/bright_cyan]'. No changes made.")
            console.print("\n[bold blue]Expected snippet:[/bold blue]")
            console.print(Panel(original_snippet, title="Expected", border_style="blue", title_align="left"))
            console.print("\n[bold blue]Actual file content:[/bold blue]")
            console.print(Panel(content, title="Actual", border_style="yellow", title_align="left"))
            return False, error_msg
            
        if occurrences > 1:
            console.print(f"[bold yellow]⚠ Multiple matches ({occurrences}) found - requiring line numbers for safety[/bold yellow]")
            console.print("[dim]Use format:\n--- original.py (lines X-Y)\n+++ modified.py[/dim]")
            error_msg = f"Ambiguous edit: {occurrences} matches"
            console.print(f"[bold yellow]⚠[/bold yellow] {error_msg} in '[bright_cyan]{path}[/bright_cyan]'. No changes made.")
            return False, error_msg
        
        updated_content = content.replace(original_snippet, new_snippet, 1)
        create_file(path, updated_content)
        success_msg = f"Applied diff edit to '{path}'"
        console.print(f"[bold blue]✓[/bold blue] {success_msg}")
        return True, success_msg

    except FileNotFoundError as e:
        error_msg = f"File not found for diff editing: '{path}'"
        console.print(f"[bold red]✗[/bold red] {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Error during diff edit: {str(e)}"
        console.print(f"[bold red]✗[/bold red] {error_msg}")
        return False, error_msg

def try_handle_add_command(user_input: str) -> bool:
    prefix = "/add "
    if user_input.strip().lower().startswith(prefix):
        path_to_add = user_input[len(prefix):].strip()
        try:
            normalized_path = normalize_path(path_to_add)
            if os.path.isdir(normalized_path):
                # Handle entire directory
                add_directory_to_conversation(normalized_path)
            else:
                # Handle a single file as before
                content = read_local_file(normalized_path)
                conversation_history.append({
                    "role": "system",
                    "content": f"Content of file '{normalized_path}':\n\n{content}"
                })
                console.print(f"[bold blue]✓[/bold blue] Added file '[bright_cyan]{normalized_path}[/bright_cyan]' to conversation.\n")
        except OSError as e:
            console.print(f"[bold red]✗[/bold red] Could not add path '[bright_cyan]{path_to_add}[/bright_cyan]': {e}\n")
        return True
    return False

def add_directory_to_conversation(directory_path: str):
    with console.status("[bold bright_blue]🔍 Scanning directory...[/bold bright_blue]") as status:
        excluded_files = {
            # Python specific
            ".DS_Store", "Thumbs.db", ".gitignore", ".python-version",
            "uv.lock", ".uv", "uvenv", ".uvenv", ".venv", "venv",
            "__pycache__", ".pytest_cache", ".coverage", ".mypy_cache",
            # Node.js / Web specific
            "node_modules", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
            ".next", ".nuxt", "dist", "build", ".cache", ".parcel-cache",
            ".turbo", ".vercel", ".output", ".contentlayer",
            # Build outputs
            "out", "coverage", ".nyc_output", "storybook-static",
            # Environment and config
            ".env", ".env.local", ".env.development", ".env.production",
            # Misc
            ".git", ".svn", ".hg", "CVS"
        }
        excluded_extensions = {
            # Binary and media files
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".avif",
            ".mp4", ".webm", ".mov", ".mp3", ".wav", ".ogg",
            ".zip", ".tar", ".gz", ".7z", ".rar",
            ".exe", ".dll", ".so", ".dylib", ".bin",
            # Documents
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            # Python specific
            ".pyc", ".pyo", ".pyd", ".egg", ".whl",
            # UV specific
            ".uv", ".uvenv",
            # Database and logs
            ".db", ".sqlite", ".sqlite3", ".log",
            # IDE specific
            ".idea", ".vscode",
            # Web specific
            ".map", ".chunk.js", ".chunk.css",
            ".min.js", ".min.css", ".bundle.js", ".bundle.css",
            # Cache and temp files
            ".cache", ".tmp", ".temp",
            # Font files
            ".ttf", ".otf", ".woff", ".woff2", ".eot"
        }
        skipped_files = []
        added_files = []
        total_files_processed = 0
        max_files = 1000  # Reasonable limit for files to process
        max_file_size = 5_000_000  # 5MB limit

        for root, dirs, files in os.walk(directory_path):
            if total_files_processed >= max_files:
                console.print(f"[bold yellow]⚠[/bold yellow] Reached maximum file limit ({max_files})")
                break

            status.update(f"[bold bright_blue]🔍 Scanning {root}...[/bold bright_blue]")
            # Skip hidden directories and excluded directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in excluded_files]

            for file in files:
                if total_files_processed >= max_files:
                    break

                if file.startswith('.') or file in excluded_files:
                    skipped_files.append(os.path.join(root, file))
                    continue

                _, ext = os.path.splitext(file)
                if ext.lower() in excluded_extensions:
                    skipped_files.append(os.path.join(root, file))
                    continue

                full_path = os.path.join(root, file)

                try:
                    # Check file size before processing
                    if os.path.getsize(full_path) > max_file_size:
                        skipped_files.append(f"{full_path} (exceeds size limit)")
                        continue

                    # Check if it's binary
                    if is_binary_file(full_path):
                        skipped_files.append(full_path)
                        continue

                    normalized_path = normalize_path(full_path)
                    content = read_local_file(normalized_path)
                    conversation_history.append({
                        "role": "system",
                        "content": f"Content of file '{normalized_path}':\n\n{content}"
                    })
                    added_files.append(normalized_path)
                    total_files_processed += 1

                except OSError:
                    skipped_files.append(full_path)

        console.print(f"[bold blue]✓[/bold blue] Added folder '[bright_cyan]{directory_path}[/bright_cyan]' to conversation.")
        if added_files:
            console.print(f"\n[bold bright_blue]📁 Added files:[/bold bright_blue] [dim]({len(added_files)} of {total_files_processed})[/dim]")
            for f in added_files:
                console.print(f"  [bright_cyan]📄 {f}[/bright_cyan]")
        if skipped_files:
            console.print(f"\n[bold yellow]⏭ Skipped files:[/bold yellow] [dim]({len(skipped_files)})[/dim]")
            for f in skipped_files[:10]:  # Show only first 10 to avoid clutter
                console.print(f"  [yellow dim]⚠ {f}[/yellow dim]")
            if len(skipped_files) > 10:
                console.print(f"  [dim]... and {len(skipped_files) - 10} more[/dim]")
        console.print()

def is_binary_file(file_path: str, peek_size: int = 1024) -> bool:
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(peek_size)
        # If there is a null byte in the sample, treat it as binary
        if b'\0' in chunk:
            return True
        return False
    except Exception:
        # If we fail to read, just treat it as binary to be safe
        return True

def ensure_file_in_context(file_path: str) -> bool:
    try:
        normalized_path = normalize_path(file_path)
        content = read_local_file(normalized_path)
        file_marker = f"Content of file '{normalized_path}'"
        if not any(file_marker in (msg["content"] or "") for msg in conversation_history):
            conversation_history.append({
                "role": "system",
                "content": f"{file_marker}:\n\n{content}"
            })
        return True
    except OSError:
        console.print(f"[bold red]✗[/bold red] Could not read file '[bright_cyan]{file_path}[/bright_cyan]' for editing context")
        return False

def normalize_path(path_str: str) -> str:
    """Return a canonical, absolute version of the path with security checks."""
    path = Path(path_str).resolve()
    
    # Prevent directory traversal attacks
    if ".." in path.parts:
        raise ValueError(f"Invalid path: {path_str} contains parent directory references")
    
    return str(path)

# --------------------------------------------------------------------------------
# 5. Conversation state
# --------------------------------------------------------------------------------
CONVERSATION_LOG_FILE = "../logs/conversation_history.log"

class ConversationHistory:
    def __init__(self, initial_history: List[Dict[str, Any]]):
        self._history = list(initial_history)
        self.whole_write()

    def _ensure_log_dir_exists(self):
        """Ensure the log directory exists."""
        log_dir = Path(CONVERSATION_LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)

    def append_write(self, record: Dict[str, Any]):
        """Append a single record to the conversation log file in JSONL format."""
        self._ensure_log_dir_exists()
        try:
            with open(CONVERSATION_LOG_FILE, "a", encoding="utf-8") as f:
                json_record = json.dumps(record)
                f.write(json_record + "\n")
        except Exception as e:
            # In a real-world scenario, you might want a more robust logging mechanism here
            console.print(f"[bold red]✗ Error writing to conversation log: {e}[/bold red]")

    def whole_write(self):
        """Overwrite the log file with the entire current conversation in JSONL format."""
        self._ensure_log_dir_exists()
        try:
            with open(CONVERSATION_LOG_FILE, "w", encoding="utf-8") as f:
                for record in self._history:
                    json_record = json.dumps(record)
                    f.write(json_record + "\n")
        except Exception as e:
            # In a real-world scenario, you might want a more robust logging mechanism here
            console.print(f"[bold red]✗ Error writing to conversation log: {e}[/bold red]")

    def append(self, item: Dict[str, Any]):
        self._history.append(item)
        self.append_write(item)

    def extend(self, items: List[Dict[str, Any]]):
        self._history.extend(items)
        self.whole_write()

    def clear(self):
        self._history.clear()
        self.whole_write()

    def __iter__(self):
        return iter(self._history)

    def __len__(self):
        return len(self._history)

    def __getitem__(self, index):
        return self._history[index]

conversation_history = ConversationHistory([
    {"role": "system", "content": system_PROMPT}
])

# --------------------------------------------------------------------------------
# 6. OpenAI API interaction with streaming
# --------------------------------------------------------------------------------

def execute_function_call_dict(tool_call_dict) -> str:
    """Execute a function call from a dictionary format and return the result as a string."""
    try:
        function_name = tool_call_dict["function"]["name"]
        arguments = json.loads(tool_call_dict["function"]["arguments"])
        
        if function_name == "read_file":
            file_path = arguments["file_path"]
            normalized_path = normalize_path(file_path)
            content = read_local_file(normalized_path)
            return f"Content of file '{normalized_path}':\n\n{content}"
            
        elif function_name == "read_multiple_files":
            file_paths = arguments["file_paths"]
            results = []
            for file_path in file_paths:
                try:
                    normalized_path = normalize_path(file_path)
                    content = read_local_file(normalized_path)
                    results.append(f"Content of file '{normalized_path}':\n\n{content}")
                except OSError as e:
                    results.append(f"Error reading '{file_path}': {e}")
            return "\n\n" + "="*50 + "\n\n".join(results)
            
        elif function_name == "create_file":
            file_path = arguments["file_path"]
            content = arguments["content"]
            create_file(file_path, content)
            return f"Successfully created file '{file_path}'"
            
        elif function_name == "create_multiple_files":
            files = arguments["files"]
            created_files = []
            for file_info in files:
                create_file(file_info["path"], file_info["content"])
                created_files.append(file_info["path"])
            return f"Successfully created {len(created_files)} files: {', '.join(created_files)}"
            
        elif function_name == "edit_file":
            file_path = arguments["file_path"]
            original_snippet = arguments["original_snippet"]
            new_snippet = arguments["new_snippet"]
            
            # Ensure file is in context first
            if not ensure_file_in_context(file_path):
                return f"Error: Could not read file '{file_path}' for editing"
            
            success, message = apply_diff_edit(file_path, original_snippet, new_snippet)
            if success:
                return f"Successfully edited file '{file_path}': {message}"
            else:
                return f"Error editing file '{file_path}': {message}"
            
        else:
            return f"Unknown function: {function_name}"
            
    except Exception as e:
        return f"Error executing {function_name}: {str(e)}"

def execute_function_call(tool_call) -> str:
    """Execute a function call and return the result as a string."""
    try:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        if function_name == "read_file":
            file_path = arguments["file_path"]
            normalized_path = normalize_path(file_path)
            content = read_local_file(normalized_path)
            return f"Content of file '{normalized_path}':\n\n{content}"
            
        elif function_name == "read_multiple_files":
            file_paths = arguments["file_paths"]
            results = []
            for file_path in file_paths:
                try:
                    normalized_path = normalize_path(file_path)
                    content = read_local_file(normalized_path)
                    results.append(f"Content of file '{normalized_path}':\n\n{content}")
                except OSError as e:
                    results.append(f"Error reading '{file_path}': {e}")
            return "\n\n" + "="*50 + "\n\n".join(results)
            
        elif function_name == "create_file":
            file_path = arguments["file_path"]
            content = arguments["content"]
            create_file(file_path, content)
            return f"Successfully created file '{file_path}'"
            
        elif function_name == "create_multiple_files":
            files = arguments["files"]
            created_files = []
            for file_info in files:
                create_file(file_info["path"], file_info["content"])
                created_files.append(file_info["path"])
            return f"Successfully created {len(created_files)} files: {', '.join(created_files)}"
            
        elif function_name == "edit_file":
            file_path = arguments["file_path"]
            original_snippet = arguments["original_snippet"]
            new_snippet = arguments["new_snippet"]
            
            # Ensure file is in context first
            if not ensure_file_in_context(file_path):
                return f"Error: Could not read file '{file_path}' for editing"
            
            success, message = apply_diff_edit(file_path, original_snippet, new_snippet)
            if success:
                return f"Successfully edited file '{file_path}': {message}"
            else:
                return f"Error editing file '{file_path}': {message}"
            
        else:
            return f"Unknown function: {function_name}"
            
    except Exception as e:
        return f"Error executing {function_name}: {str(e)}"

def log_stream_chunk(chunk: ChatCompletionChunk):
    """Append a single stream chunk to the stream log file in JSONL format."""
    log_dir = Path("../logs/")
    log_dir.mkdir(parents=True, exist_ok=True)
    try:
        with open("../logs/stream_chunks.log", "a", encoding="utf-8") as f:
            # Pydantic models have a .model_dump() method for serialization
            # Using exclude_unset=True keeps the log clean by not writing null values
            chunk_dict = chunk.model_dump(exclude_unset=True)
            if not chunk_dict:  # Don't log empty chunks
                return
            
            json_record = json.dumps(chunk_dict)
            f.write(json_record + "\n")
    except Exception as e:
        # Avoid crashing the main loop for a logging error
        console.print(f"[bold red]✗ Error writing to stream log: {e}[/bold red]")

def process_streaming_response(stream, stream_name="response"):
    """Process a streaming response and extract content and tool calls."""
    console.print(f"\n[bold bright_blue]📡 Processing {stream_name} stream...[/bold bright_blue]")
    
    reasoning_started = False
    content = ""
    tool_calls = []
    
    for chunk in stream:
        log_stream_chunk(chunk)
        
        # Handle reasoning content if available (DeepSeek-specific)
        if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
            if not reasoning_started:
                console.print("\n[bold blue]💭 Reasoning:[/bold blue]")
                reasoning_started = True
            console.print(chunk.choices[0].delta.reasoning_content, end="")
            
        # Handle regular content
        elif chunk.choices[0].delta.content:
            if reasoning_started:
                console.print("\n")
                console.print(f"\n[bold bright_blue]🤖 {stream_name.title()}>[/bold bright_blue] ", end="")
                reasoning_started = False
            content += chunk.choices[0].delta.content
            console.print(chunk.choices[0].delta.content, end="")
            
        # Handle tool calls
        elif chunk.choices[0].delta.tool_calls:
            for tool_call_delta in chunk.choices[0].delta.tool_calls:
                if tool_call_delta.index is not None:
                    # Ensure we have enough tool_calls
                    while len(tool_calls) <= tool_call_delta.index:
                        tool_calls.append({
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        })
                    
                    if tool_call_delta.id:
                        tool_calls[tool_call_delta.index]["id"] = tool_call_delta.id
                    if tool_call_delta.function:
                        if tool_call_delta.function.name:
                            tool_calls[tool_call_delta.index]["function"]["name"] += tool_call_delta.function.name
                        if tool_call_delta.function.arguments:
                            tool_calls[tool_call_delta.index]["function"]["arguments"] += tool_call_delta.function.arguments
    
    
        elif isinstance(chunk, ChatCompletionChunk):
            console.print(f"   ChatComplete {stream_name}")

        else:
            console.print(f"  ELSE>> {stream_name}. ClassName: {chunk.__class__.__name__}, Namespace: {chunk.__class__.__module__}, delta: {chunk.choices[0].delta}   chunk: {chunk}")

    console.print(f"\n>> {stream_name} stream complete")
    console.print(f"   - Content length: {len(content)}")
    console.print(f"   - Tool calls found: {len(tool_calls)}")
    
    return content, tool_calls

def format_and_execute_tool_calls(tool_calls, call_prefix="call"):
    """Format tool calls and execute them, returning the formatted calls and results."""
    if not tool_calls:
        return [], []
    
    console.print(f"\n[bold bright_cyan]⚡ Executing {len(tool_calls)} function call(s)...[/bold bright_cyan]")
    
    formatted_tool_calls = []
    tool_results = []
    
    for i, tc in enumerate(tool_calls):
        if tc["function"]["name"]:  # Only process if we have a function name
            # Ensure we have a valid tool call ID
            tool_id = tc["id"] if tc["id"] else f"{call_prefix}_{i}_{int(time.time() * 1000)}"
            
            formatted_tool_call = {
                "id": tool_id,
                "type": "function",
                "function": {
                    "name": tc["function"]["name"],
                    "arguments": tc["function"]["arguments"]
                }
            }
            formatted_tool_calls.append(formatted_tool_call)
            
            console.print(f"[bright_blue]→ {tc['function']['name']}[/bright_blue]")
            console.print(f"   Args: {tc['function']['arguments'][:100]}{'...' if len(tc['function']['arguments']) > 100 else ''}")
            
            try:
                result = execute_function_call_dict(formatted_tool_call)
                
                tool_response = {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": result
                }
                tool_results.append(tool_response)
                
                # Check if the result indicates an error
                if result.startswith("Error"):
                    console.print(f"   ✗ Error: {result[:100]}{'...' if len(result) > 100 else ''}")
                else:
                    console.print(f"   ✓ Success: {result[:100]}{'...' if len(result) > 100 else ''}")
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                tool_response = {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": error_msg
                }
                tool_results.append(tool_response)
                console.print(f"   ✗ Exception: {e}")
    
    return formatted_tool_calls, tool_results

def create_assistant_message(content, tool_calls=None):
    """Create a properly formatted assistant message."""
    message = {
        "role": "assistant",
        "content": content if content else None
    }
    
    if tool_calls:
        message["tool_calls"] = tool_calls
        # When there are tool calls, content should be None if empty
        if not content:
            message["content"] = None
    
    return message

def trim_conversation_history():
    """Trim conversation history to prevent token limit issues while preserving tool call sequences"""
    if len(conversation_history) <= 20:  # Don't trim if conversation is still small
        return
        
    # Always keep the system prompt
    system_msgs = [msg for msg in conversation_history if msg["role"] == "system"]
    other_msgs = [msg for msg in conversation_history if msg["role"] != "system"]
    
    # Keep only the last 15 messages to prevent token overflow
    if len(other_msgs) > 15:
        other_msgs = other_msgs[-15:]
    
    # Rebuild conversation history
    conversation_history.clear()
    conversation_history.extend(system_msgs + other_msgs)

def stream_openai_response(user_message: str):
    console.print(f"\n[bold bright_blue]🐋 Starting conversation round...[/bold bright_blue]")
    console.print(f"   User message: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
    
    # Add the user message to conversation history
    conversation_history.append({"role": "user", "content": user_message})
    
    # Trim conversation history if it's getting too long
    trim_conversation_history()
    console.print(f"   Conversation history length: {len(conversation_history)} messages")

    try:

        # Main conversation loop - handle multiple rounds of tool calls
        round_number = 1
        max_rounds = 10  # Prevent infinite loops
        
        while round_number <= max_rounds:
            console.print(f"\n[bold bright_cyan]🔄 Round {round_number}/{max_rounds}[/bold bright_cyan]")
            
            # Create API call
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=conversation_history,
                tools=tools,
                stream=True
            )
            
            # Process the streaming response
            content, tool_calls = process_streaming_response(stream, f"round-{round_number}")

            # Handle the response
            if tool_calls:
                console.print(f"\n[bold yellow]🔧 Tool calls detected in round {round_number}[/bold yellow]")
                
                # Format and execute tool calls
                formatted_tool_calls, tool_results = format_and_execute_tool_calls(
                    tool_calls, f"round{round_number}"
                )
                
                if formatted_tool_calls:
                    # Create and store assistant message with tool calls
                    assistant_message = create_assistant_message(content, formatted_tool_calls)
                    conversation_history.append(assistant_message)
                    console.print(f"   Added assistant message with {len(formatted_tool_calls)} tool calls")
                    
                    # Add all tool results to conversation
                    for tool_result in tool_results:
                        conversation_history.append(tool_result)
                    console.print(f"   Added {len(tool_results)} tool results")
                    
                    # Continue to next round to get follow-up response
                    round_number += 1
                    continue
                else:
                    console.print(f"   No valid tool calls found, ending conversation")
                    break
            else:
                # No tool calls, this is the final response
                console.print(f"\n[bold green]✅ Final response received in round {round_number}[/bold green]")
                if content:
                    assistant_message = create_assistant_message(content)
                    conversation_history.append(assistant_message)
                    console.print(f"   Added final assistant message: {content[:100]}{'...' if len(content) > 100 else ''}")
                break
        
        if round_number > max_rounds:
            console.print(f"\n[bold red]⚠️ Maximum rounds ({max_rounds}) reached, stopping conversation[/bold red]")
            # Add a final message explaining the termination
            conversation_history.append({
                "role": "assistant", 
                "content": "I've reached the maximum number of tool call rounds. The conversation has been terminated to prevent infinite loops."
            })

        console.print(f"\n[bold bright_blue]🏁 Conversation completed after {round_number} rounds[/bold bright_blue]")
                

        return {"success": True}

    except Exception as e:
        error_msg = f"OpenAI API error: {str(e)}"
        console.print(f"\n[bold red]❌ {error_msg}[/bold red]")
        return {"error": error_msg}

# --------------------------------------------------------------------------------
# 7. Main interactive loop
# --------------------------------------------------------------------------------

def main():
    # Check for command line arguments
    import sys
    
    run_interactive_mode()

    # if len(sys.argv) > 1:
    #     # Handle other commands passed as arguments
    #     command = sys.argv[1]
    #     if command == "interactive":
    #         run_interactive_mode()
    #         return
    #     else:
    #         console.print(f"[bold red]❌ Unknown command: {command}[/bold red]")
    #         console.print("[dim]Available commands: interactive[/dim]")
    #         return
    
    # # Default mode: look for TASK.md file
    # task_file = "TASK.md"
    
    # try:
    #     if not os.path.exists(task_file):
    #         # Check in input subdirectory as well
    #         task_file = "input/TASK.md"
    #         if not os.path.exists(task_file):
    #             console.print(f"[bold red]❌ No TASK.md file found in current directory or input/ subdirectory[/bold red]")
    #             return
        
    #     # Read the task file
    #     with open(task_file, 'r', encoding='utf-8') as f:
    #         task_content = f.read().strip()
        
    #     if not task_content:
    #         console.print(f"[bold red]❌ TASK.md file is empty[/bold red]")
    #         return
        
    #     console.print(f"[bold bright_blue]🤖 AI Agent Starting Task[/bold bright_blue]")
    #     console.print(f"[dim]Reading task from: {task_file}[/dim]")
    #     console.print(Panel(
    #         task_content,
    #         title="[bold blue]📋 Task Description[/bold blue]",
    #         border_style="blue",
    #         padding=(1, 2)
    #     ))
        
    #     # Process the task
    #     response_data = stream_openai_response(task_content)
        
    #     if response_data.get("error"):
    #         console.print(f"[bold red]❌ Error: {response_data['error']}[/bold red]")
    #         sys.exit(1)
    #     else:
    #         console.print(f"\n[bold green]✅ Task completed successfully[/bold green]")
    #         sys.exit(0)
            
    # except Exception as e:
    #     console.print(f"[bold red]❌ Error reading task file: {str(e)}[/bold red]")
    #     sys.exit(1)

def run_interactive_mode():
    """Run the original interactive mode"""
    # Create a beautiful gradient-style welcome panel
    welcome_text = """[bold bright_blue]🐋 DeepSeek Engineer[/bold bright_blue] [bright_cyan]with Function Calling[/bright_cyan]
[dim blue]Powered by DeepSeek-R1 with Chain-of-Thought Reasoning[/dim blue]"""
    
    console.print(Panel.fit(
        welcome_text,
        border_style="bright_blue",
        padding=(1, 2),
        title="[bold bright_cyan]🤖 AI Code Assistant[/bold bright_cyan]",
        title_align="center"
    ))
    
    # Create an elegant instruction panel
    instructions = """[bold bright_blue]📁 File Operations:[/bold bright_blue]
  • [bright_cyan]/add path/to/file[/bright_cyan] - Include a single file in conversation
  • [bright_cyan]/add path/to/folder[/bright_cyan] - Include all files in a folder
  • [dim]The AI can automatically read and create files using function calls[/dim]

[bold bright_blue]🎯 Commands:[/bold bright_blue]
  • [bright_cyan]exit[/bright_cyan] or [bright_cyan]quit[/bright_cyan] - End the session
  • Just ask naturally - the AI will handle file operations automatically!"""
    
    console.print(Panel(
        instructions,
        border_style="blue",
        padding=(1, 2),
        title="[bold blue]💡 How to Use[/bold blue]",
        title_align="left"
    ))
    console.print()

    while True:
        try:
            user_input = prompt_session.prompt("🔵 You> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold yellow]👋 Exiting gracefully...[/bold yellow]")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            console.print("[bold bright_blue]👋 Goodbye! Happy coding![/bold bright_blue]")
            break

        if try_handle_add_command(user_input):
            continue

        response_data = stream_openai_response(user_input)
        
        if response_data.get("error"):
            console.print(f"[bold red]❌ Error: {response_data['error']}[/bold red]")

    console.print("[bold blue]✨ Session finished. Thank you for using DeepSeek Engineer![/bold blue]")

if __name__ == "__main__":
    main()

import requests
import json
import os
import subprocess
import sys
import threading
import time
import random
from ddgs import DDGS

# --- Configuration ---
OLLAMA_URL = "http://10.99.99.99:11434/api/chat"
MODEL = "qwen3.5:latest"
WORKSPACE = "/home/noob/agents/ai_workspace"

if not os.path.exists(WORKSPACE):
    os.makedirs(WORKSPACE)

DUKE_PHRASES = [
    "Duke is loading his shotgun...",
    "Duke is chewing gum...",
    "Duke is checking the perimeter...",
    "Duke is taking names...",
    "Duke is out of gum...",
    "Duke is scouting for alien scum..."
]

class Spinner:
    """A thread-safe spinner with a smooth 'breathing' green pulse."""
    def __init__(self):
        self.message = random.choice(DUKE_PHRASES)
        self.stop_running = threading.Event()
        self.thread = threading.Thread(target=self._spin)
        
        # ANSI 256-color shades of green (from dark to bright)
        self.pulse_shades = [22, 28, 34, 40, 46, 82, 46, 40, 34, 28]
        self.reset = "\033[0m"

    def _spin(self):
        chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        frame = 0
        
        while not self.stop_running.is_set():
            # Calculate color based on pulse index
            color_code = self.pulse_shades[frame % len(self.pulse_shades)]
            char = chars[frame % len(chars)]
            
            # Apply color to the whole line for a smooth glow effect
            # \033[38;5;Nm sets the 256-color foreground
            sys.stdout.write(f"\r\033[38;5;{color_code}m{char} {self.message}{self.reset}")
            sys.stdout.flush()
            
            frame += 1
            time.sleep(0.08) # Slightly faster for smoother transitions
                
            if self.stop_running.is_set():
                break
                    
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.stop_running.set()
        self.thread.join()

# --- Tool Functions ---

def write_file(filename, content):
    path = os.path.join(WORKSPACE, os.path.basename(filename))
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"SUCCESS: File created at {path}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def read_file(filename):
    path = os.path.join(WORKSPACE, os.path.basename(filename))
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            return f"ERROR: {str(e)}"
    return "ERROR: File not found."

def run_command(command):
    print(f"\n[*] Action Hero Terminal: {command}")
    try:
        process = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd=WORKSPACE, timeout=60
        )
        return f"STDOUT: {process.stdout}\nSTDERR: {process.stderr}"
    except Exception as e:
        return f"EXECUTION ERROR: {str(e)}"

def web_search(query):
    print(f"\n[*] Duke is scouting: {query}")
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                results.append(r)
        return json.dumps(results)
    except Exception as e:
        return f"SEARCH ERROR: {str(e)}"

def run_duke_loop(user_input):
    messages = [{"role": "user", "content": user_input}]
    for _ in range(5):
        payload = {"model": MODEL, "messages": messages, "tools": TOOLS, "stream": False}
        with Spinner():
            try:
                response = requests.post(OLLAMA_URL, json=payload).json()
            except Exception as e:
                print(f"\nConnection Error: {e}")
                break

        msg = response.get("message", {})
        messages.append(msg)
        if not msg.get("tool_calls"):
            print(f"\n\033[1;32m[Duke]:\033[0m {msg.get('content', '')}")
            break

        for tool in msg["tool_calls"]:
            fn_name = tool["function"]["name"]
            args = tool["function"]["arguments"]
            if isinstance(args, str):
                try: args = json.loads(args)
                except: continue
            
            if fn_name == "write_file": res = write_file(**args)
            elif fn_name == "read_file": res = read_file(**args)
            elif fn_name == "run_command": res = run_command(**args)
            elif fn_name == "web_search": res = web_search(**args)
            messages.append({"role": "tool", "content": str(res)})

TOOLS = [
    {"type": "function", "function": {"name": "write_file", "description": "Create a file", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "content": {"type": "string"}}, "required": ["filename", "content"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a file", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": ["filename"]}}},
    {"type": "function", "function": {"name": "run_command", "description": "Run a bash command", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "web_search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}
]

if __name__ == "__main__":
    print("\033[1;32m--- DUKE NUKEM: TACTICAL MODE ACTIVE ---\033[0m")
    while True:
        try:
            inp = input("\nYou: ")
            if inp.lower() in ['exit', 'quit']: break
            run_duke_loop(inp)
        except KeyboardInterrupt: break

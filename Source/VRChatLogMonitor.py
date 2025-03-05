import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import json
import time
import threading
import os
import datetime
import glob
import queue
import asyncio
import discord

# Load configuration
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# Determine log directory and pattern from config.
log_dir = config.get("log_directory", "")
log_pattern = config.get("log_pattern", "output_log_*.txt")
output_log_prefix = config.get("output_log_prefix", "parsed_log_")
discord_config = config.get("discord", {})
event_configs = config.get("events", {})

# Create a thread-safe queue for Discord messages.
# Each item in the queue will be a tuple: (message, hex_color)
discord_message_queue = queue.Queue()

def get_latest_log_file():
    """
    Searches for files matching the given pattern in log_dir.
    Returns the newest file based on modification time.
    """
    log_dir_expanded = os.path.expandvars(log_dir)
    pattern = os.path.join(log_dir_expanded, log_pattern)
    matching_files = glob.glob(pattern)
    if not matching_files:
        return None
    latest_file = max(matching_files, key=os.path.getmtime)
    return latest_file

def get_output_log_filename():
    """
    Returns the output log filename with current date appended.
    Format: parsed_log_YYYY-MM-DD.txt
    """
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    return f"{output_log_prefix}{current_date}.txt"

def enqueue_discord_message(message, hex_color):
    """Place a message and its color into the Discord message queue."""
    if discord_config.get("enabled", False):
        discord_message_queue.put((message, hex_color))

# ------------------------------------------------------------------------------
# Discord Bot Integration using discord.py
# ------------------------------------------------------------------------------

class DiscordBotClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        # Start the background task that sends queued messages.
        self.bg_task = self.loop.create_task(self.send_messages_from_queue())

    async def send_messages_from_queue(self):
        await self.wait_until_ready()
        channel_id = int(discord_config.get("channel_id", 0))
        channel = self.get_channel(channel_id)
        if channel is None:
            print("Channel not found. Check your channel_id in config.")
            return
        while not self.is_closed():
            try:
                # Try to get a message without blocking.
                message, hex_color = discord_message_queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(1)
            else:
                try:
                    # Convert hex color (e.g., "#008000") to an integer.
                    color_value = int(hex_color.lstrip('#'), 16)
                    embed = discord.Embed(description=message, color=color_value)
                    await channel.send(embed=embed)
                except Exception as e:
                    print("Error sending message to Discord:", e)

def start_discord_bot():
    """Starts the Discord bot client in a separate thread."""
    bot_token = discord_config.get("bot_token")
    if not bot_token:
        print("No bot token provided in config.")
        return
    intents = discord.Intents.default()  # Adjust intents as needed.
    client = DiscordBotClient(intents=intents)
    client.run(bot_token)

# ------------------------------------------------------------------------------
# Tkinter Log Monitor
# ------------------------------------------------------------------------------

class LogMonitor(threading.Thread):
    """Background thread that tails the newest VRChat log file and processes new lines."""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self._stop_event = threading.Event()
        self.log_file_path = None

    def run(self):
        # Wait until the newest log file becomes available.
        while not self._stop_event.is_set():
            self.log_file_path = get_latest_log_file()
            if self.log_file_path:
                break
            time.sleep(1)
        if not self.log_file_path:
            print("No log file found.")
            return

        print("Monitoring log file:", self.log_file_path)
        with open(self.log_file_path, "r", encoding="utf-8", errors="ignore") as f:
            # Move to the end of the file to avoid processing old entries.
            f.seek(0, os.SEEK_END)
            while not self._stop_event.is_set():
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                self.process_line(line)

    def process_line(self, line):
        """
        Check for configured events in the line.
        If an event is detected:
          - Timestamp the line.
          - Log it to a date-based file.
          - Display it in the GUI.
          - Enqueue a Discord message with the event's color.
        """
        for event_name, event_data in event_configs.items():
            if event_name in line:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                output_line = f"{timestamp} - {line}"
                # Append to the dynamically-named output log file.
                output_log_filename = get_output_log_filename()
                with open(output_log_filename, "a", encoding="utf-8") as log_out:
                    log_out.write(output_line)
                # Display in the GUI with event-specific tag (color).
                self.text_widget.insert(tk.END, output_line, event_name)
                self.text_widget.see(tk.END)
                # Enqueue the message for Discord along with the event's hex color.
                hex_color = event_data.get("color", "#FFFFFF")
                enqueue_discord_message(output_line, hex_color)
                break

    def stop(self):
        self._stop_event.set()

def setup_text_tags(text_widget):
    """Configure text tags for each event to display them in different colors."""
    for event_name, event_data in event_configs.items():
        color = event_data.get("color", "black")
        text_widget.tag_config(event_name, foreground=color)

def on_closing(root, monitor_thread):
    monitor_thread.stop()
    root.destroy()

def main():
    # Start the Discord bot in a separate thread.
    discord_thread = threading.Thread(target=start_discord_bot, daemon=True)
    discord_thread.start()
    
    # Create the main Tkinter window.
    root = tk.Tk()
    root.title("VRChat Log Monitor")
    text_widget = ScrolledText(root, width=100, height=30)
    text_widget.pack(fill=tk.BOTH, expand=True)
    
    setup_text_tags(text_widget)
    
    # Start the log monitoring thread.
    monitor_thread = LogMonitor(text_widget)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Ensure graceful exit.
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, monitor_thread))
    root.mainloop()

if __name__ == "__main__":
    main()

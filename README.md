![image](https://github.com/user-attachments/assets/eb8c2341-7386-46f0-b0b8-04eceaf421b1)

# VRChat Log Monitor

This project is a real-time VRChat log monitor built with Python and Tkinter. It monitors the latest VRChat log file (matching `output_log_*.txt`), parses events based on configurable keywords, logs them with timestamps to a date-based file, displays the events in a GUI with color-coding, and posts event notifications to a Discord channel using a Discord bot powered by discord.py.

## Features

- **Real-time Log Monitoring:** Tails the newest VRChat log file.
- **Event Parsing:** Detects events (e.g., `OnPlayerJoined`, `OnPlayerLeft`, etc.) defined in the configuration.
- **GUI Display:** Uses Tkinter to display events with event-specific colors.
- **Log Output:** Writes parsed events with timestamps to a file named with the current date (e.g., `parsed_log_2025-03-04.txt`).
- **Discord Integration:** Posts notifications as Discord embeds with colors matching the event definitions.

## Prerequisites

- Python 3.6 or higher
- [discord.py](https://discordpy.readthedocs.io/) (for Discord integration)
- [requests](https://pypi.org/project/requests/) (if you need it elsewhere)



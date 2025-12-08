#!/usr/bin/env python3
"""Simple cron test - prints current time"""

from datetime import datetime
import sys

def main():
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"Cron job executed at: {current_time}")
    sys.stdout.flush()

if __name__ == "__main__":
    main()

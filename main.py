#!/usr/bin/env python3
"""
AurumBotX su Replit
Avvio automatico per team access
"""

import os
import subprocess
import sys

def main():
    print("🚀 Avvio AurumBotX su Replit...")
    
    # Avvia server
    os.system("python3 standalone_server.py 8080")

if __name__ == "__main__":
    main()

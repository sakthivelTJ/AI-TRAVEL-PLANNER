#!/usr/bin/env python3
import os
import sys

# Make sure we load from fresh
if '.env' in sys.modules:
    del sys.modules['.env']

from dotenv import load_dotenv

# Reload the env file
load_dotenv('.env', override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"[CHECK] Full API Key from .env: {GEMINI_API_KEY}")
print(f"[CHECK] API Key length: {len(GEMINI_API_KEY) if GEMINI_API_KEY else 0}")
print(f"[CHECK] API Key starts with: {GEMINI_API_KEY[:20] if GEMINI_API_KEY else 'NONE'}")

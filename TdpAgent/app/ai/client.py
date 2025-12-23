from __future__ import annotations
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load .env once when this module is imported
load_dotenv()

def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing in .env")
    return OpenAI(api_key=api_key)

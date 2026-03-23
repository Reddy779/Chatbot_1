import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()  # Reads .env file into os.environ

# Client created once at module load — not per request
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL  = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = """You are a helpful, concise, and friendly assistant.
Always respond in clear plain text."""

def get_response(history: list[dict]) -> str:
    """
    Sends conversation history to Groq and returns
    the full assistant reply as a plain string.

    history: list of {"role": "user"/"assistant", "content": "..."}
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )

    return completion.choices[0].message.content
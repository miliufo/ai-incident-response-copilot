import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing. Add it to your .env file."
    )

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

MODEL_NAME = "openai/gpt-oss-20b"


def get_llm():
    """
    Return the shared OpenAI-compatible Groq client.
    """
    return client
import os
import time
from groq import Groq

def get_llm_response(prompt: str, system_instruction: str = None) -> str:
    """
    Calls the Groq API to get a response.
    Ensure that the GROQ_API_KEY environment variable is set.
    """
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key or api_key in ("your_api_key_here", "<your_api_key_here>"):
        raise ValueError("GROQ_API_KEY is missing or still set to the placeholder in .env. Please update .env with your valid Groq API key.")

    client = Groq(api_key=api_key)
    
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
        
    messages.append({"role": "user", "content": prompt})

    # Default to high-performance active Groq models
    candidate_models = [
        os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b"
    ]
        
    max_retries = 3
    for attempt in range(max_retries):
        model_name = candidate_models[min(attempt, len(candidate_models) - 1)]
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"\n[Warning] API Error with model {model_name} (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print("Sleeping for 3 seconds before retrying...")
                time.sleep(3)
            else:
                print("Max retries reached. Please verify your GROQ_API_KEY and model permissions.")
                raise

import os
import time
from groq import Groq

def get_llm_response(prompt: str, system_instruction: str = None) -> str:
    """
    Calls the Groq API to get a response.
    Ensure that the GROQ_API_KEY environment variable is set.
    """
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
        
    messages.append({"role": "user", "content": prompt})
        
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Using the fast OSS model
            response = client.chat.completions.create(
                model='openai/gpt-oss-120b',
                messages=messages,
                temperature=0.2 # Low temperature for more deterministic coding output
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"\n⚠️ API Error (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print("⏳ Sleeping for 10 seconds before retrying...")
                time.sleep(10)
            else:
                print("❌ Max retries reached. Please ensure your GROQ_API_KEY is valid.")
                raise

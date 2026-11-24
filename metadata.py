import os
import time
from dotenv import load_dotenv
from google import genai

# Load API key
load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-3.5-flash"

# Track users during this program session
users = set()

print("===== GEMINI API CONCEPTS =====")

while True:
    user_id = input("\nEnter your user ID (or 'exit'): ")

    if user_id.lower() == "exit":
        break

    users.add(user_id)

    question = input("Enter your question: ")

    # 1. Count input tokens
    token_result = client.models.count_tokens(
        model=MODEL,
        contents=question
    )

    print("\n1. INPUT TOKEN COUNT")
    print("Tokens:", token_result.total_tokens)

    # 2. Generate response and measure time
    start_time = time.perf_counter()

    response = client.models.generate_content(
        model=MODEL,
        contents=question
    )

    end_time = time.perf_counter()

    print("\n2. GEMINI RESPONSE")
    print(response.text)

    # 3. Response metadata
    metadata = response.usage_metadata

    print("\n3. RESPONSE METADATA")
    if metadata:
        print("Prompt tokens:", metadata.prompt_token_count)
        print("Output tokens:", metadata.candidates_token_count)
        print("Total tokens:", metadata.total_token_count)

    # 4. Time logic
    elapsed = end_time - start_time

    print("\n4. TIME LOGIC")
    print(f"Response time: {elapsed:.2f} seconds")

    # 5. User count
    print("\n5. USER COUNT")
    print("Unique users in this session:", len(users))

print("\nProgram completed!")
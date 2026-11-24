from datetime import datetime, timedelta, timezone
import os
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

MODEL_ID = "gemini-3.5-flash-lite"
CHATS_PER_PAGE = 3
SYSTEM_INSTRUCTION = "You are a helpful assistant."


def get_api_key() -> str:
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY கிடைக்கவில்லை! .env கோப்பில் அல்லது PowerShell-ல் GEMINI_API_KEY அமைக்கவும்."
        )
    return api_key


def get_tamil_nadu_now() -> str:
    try:
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
    except ZoneInfoNotFoundError:
        ist_fixed = timezone(timedelta(hours=5, minutes=30), name="IST")
        now = datetime.now(ist_fixed)
    return now.strftime("%A, %B %d, %Y at %I:%M %p IST")


def build_config(use_search: bool = False) -> types.GenerateContentConfig:
    tn_now = get_tamil_nadu_now()
    tools = [types.Tool(google_search=types.GoogleSearch())] if use_search else None
    return types.GenerateContentConfig(
        system_instruction=(
            f"{SYSTEM_INSTRUCTION} Current local date and time in Tamil Nadu: {tn_now}."
        ),
        tools=tools,
    )


def open_new_page(client: genai.Client, page_number: int, use_search: bool = False):
    print("\n" + "=" * 60)
    print(f"📄 NEW PAGE {page_number} OPENED | {get_tamil_nadu_now()}")
    print("=" * 60 + "\n")
    return client.chats.create(
        model=MODEL_ID,
        config=build_config(use_search=use_search),
    )


def safe_count_tokens(client: genai.Client, contents) -> int:
    if not contents:
        return 0
    try:
        info = client.models.count_tokens(model=MODEL_ID, contents=contents)
        return info.total_tokens or 0
    except errors.APIError as e:
        print(f"[Token Count Warning: {e}]")
        return 0


def main() -> None:
    client = genai.Client(api_key=get_api_key())

    search_enabled = False
    page_number = 1
    chats_in_current_page = 0
    total_session_tokens = 0

    chat = open_new_page(client, page_number, use_search=search_enabled)
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        user_input = input(f"[Page {page_number} | Chat {chats_in_current_page + 1}/{CHATS_PER_PAGE}] You: ").strip()
        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            remaining_tokens = safe_count_tokens(client, chat.get_history())
            print(
                f"\n[Session Closed | Page {page_number} Tokens: {remaining_tokens} | "
                f"Total Session Tokens: {total_session_tokens}]"
            )
            break

        try:
            response = chat.send_message(user_input)
        except errors.ClientError as e:
            if e.code == 429:
                print(
                    "\n[Error 429: Quota exceeded. Check https://aistudio.google.com/rate-limit "
                    "or switch API key/model.]\n"
                )
                continue
            raise

        reply_text = response.text or "[Empty response received]"
        print(f"\nGemini: {reply_text}\n")

        usage = response.usage_metadata
        input_tokens = (usage.prompt_token_count or 0) if usage else 0
        output_tokens = (usage.candidates_token_count or 0) if usage else 0
        turn_tokens = (
            (usage.total_token_count or (input_tokens + output_tokens)) if usage else 0
        )
        total_session_tokens += turn_tokens
        chats_in_current_page += 1

        print(
            f"[Chat {chats_in_current_page}/{CHATS_PER_PAGE} Tokens -> "
            f"Input: {input_tokens} | Output: {output_tokens} | Turn Total: {turn_tokens}]"
        )

        # 3 chats முடிந்தவுடன் tokens எண்ணி New Page திறக்கும்
        if chats_in_current_page >= CHATS_PER_PAGE:
            page_tokens = safe_count_tokens(client, chat.get_history())
            print(
                f"\n✅ Page {page_number} completed ({CHATS_PER_PAGE} chats). "
                f"Page {page_number} Total History Tokens: {page_tokens}"
            )
            page_number += 1
            chats_in_current_page = 0
            chat = open_new_page(client, page_number, use_search=search_enabled)

        time.sleep(1)


if __name__ == "__main__":
    main()
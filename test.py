import sys
from tildee import TildesClient
import time

t = TildesClient(
    "user", "blobblob", base_url="https://localhost:4443", verify_ssl=False
)

while True:
    unread_message_ids = t.fetch_unread_message_ids()
    for mid in unread_message_ids:
        conversation = t.fetch_conversation(mid)
        text = conversation.entries[-1].content_html
        if conversation.entries[-1].author == t.username:
            break
        print(f"Found a message by {conversation.entries[-1].author}")
        if "hello there" in text.lower():
            print("Replying…")
            t.create_message(
                mid, f"General {conversation.entries[-1].author}! You are a bold one."
            )
        time.sleep(3)
    time.sleep(60)

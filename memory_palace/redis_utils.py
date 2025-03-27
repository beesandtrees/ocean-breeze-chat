import asyncio
import redis
import time
import json
from redis.commands.json.path import Path
from metadata_utils import analyze_conversation, extract_topics_from_input, generate_word_count_metadata

r = redis.Redis(host='redis', port=6379, decode_responses=True)
if not r.exists('chat_id_counter'):
    r.set('chat_id_counter', 0)


def add_conversation_to_short_term(conversation):
    try:
        chat_id = f"chat:{r.incr('chat_id_counter')}"
        # Add the conversation to sorted set with timestamp as score
        r.zadd('recent_conversations', {chat_id: int(time.time())})
        # Store the conversation as JSON in a hash
        conversation_json = json.dumps(conversation)
        r.hset(chat_id, mapping={"conversation": conversation_json})
    except (redis.RedisError, json.JSONDecodeError) as e:
        print(f"Error in add_conversation_to_short_term: {e}")
        return None


async def augment_with_metadata(chat_id, conversation, user_id):
    messages = [f"{entry['role']}: {entry['content']}" for entry in conversation]
    full_text = " ".join(messages)

    # Generate metadata
    metadata = analyze_conversation(conversation)

    chat_log = {
        "chat": full_text,
        "user_id": user_id,
        "summary": metadata.get("summary", "No summary"),
        "sentiment": metadata.get("sentiment", "neutral"),
        "word_count": generate_word_count_metadata(conversation),
        "topics": metadata.get("topics", []),
        "key_entities": metadata.get("key_entities", []),
        "timestamp": int(time.time())
    }

    r.json().set(chat_id, Path.root_path(), chat_log)
    print(f"Metadata augmented for chat ID: {chat_id}")


async def process_conversation_for_long_term():
    while True:
        chat_ids = r.zrange('recent_conversations', -1, -1)
        if chat_ids:
            chat_id = chat_ids[0]
            conversation = r.hget(chat_id, "conversation")
            user_id = r.hget(chat_id, "user_id")
            await augment_with_metadata(chat_id, conversation, user_id)
            r.zrem('recent_conversations', chat_id)
            r.zadd('long_term_conversations', {chat_id: int(time.time())})
        await asyncio.sleep(1)  # Adjust sleep interval as needed


def get_top_10_conversations():
    # Retrieve the top 10 chat IDs from the sorted set
    chat_ids = r.zrevrange('recent_conversations', 0, 9)

    # Fetch the conversations from the hash
    conversations = []
    for chat_id in chat_ids:
        conversation_json = r.hget(chat_id, "conversation")
        if conversation_json:
            conversation = json.loads(conversation_json)
            conversations.append(conversation)  # Append each conversation as a nested list

    # Reverse the order of the nested lists
    conversations.reverse()

    # Flatten the list of conversations
    flattened_conversations = [item for sublist in conversations for item in sublist]

    return flattened_conversations


def search_related_conversations(topic):
    # Search for conversations with the given topic
    query = f"@topics:{{{topic}}}"
    search_results = r.ft("idx:chats").search(query)
    return [doc.summary for doc in search_results.docs]


def get_memory_for_input(user_input):
    # Extract topics from the user input
    topics = extract_topics_from_input(user_input)

    # Retrieve recent conversations
    recent_conversations = get_top_10_conversations()

    # Retrieve related conversations based on topics
    related_conversations = []
    for topic in topics:
        related_conversations.extend(search_related_conversations(topic))

    return {
        "recent_conversations": recent_conversations,
        "related_conversations": related_conversations
    }


def check_key_existence(chat_id):
    exists = r.exists(chat_id)
    print(f"Key {chat_id} exists: {exists}")
    return exists


def verify_data_storage(chat_id):
    stored_conversation = r.hget(chat_id, "conversation")
    print(f"Stored conversation for {chat_id}: {stored_conversation}")

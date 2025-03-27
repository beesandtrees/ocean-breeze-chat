import redis
r = redis.Redis(host='redis', port=6379, decode_responses=True)


def create_summary(conversation):
    # Implement your summary logic here
    return conversation[:100]  # Example summary


def weed_memory():
    conversation_ids = r.zrange('long_term_conversations', 0, -1)
    for chat_id in conversation_ids:
        conversation = r.hget(chat_id, "conversation")
        if "greeting" in conversation:
            r.delete(chat_id)
            r.zrem('long_term_conversations', chat_id)
        else:
            summary = create_summary(conversation)
            r.hset(chat_id, "summary", summary)

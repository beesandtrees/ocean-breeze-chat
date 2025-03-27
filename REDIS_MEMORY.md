# Enhanced Conversational Memory with Redis

This document explains how to use the enhanced conversational memory features in Ocean Chat.

## Overview

The enhanced memory system provides:

1. **Topic-based retrieval** - Store and retrieve conversations based on topics
2. **Metadata extraction** - Extract useful information from conversations
3. **Memory management** - Organize conversations into short-term and long-term memory
4. **Contextual responses** - Enhance chat responses with relevant past conversations

## How It Works

When a user sends a message to any chat client, the system:

1. Stores the message and response in Redis
2. Extracts topics and metadata from the conversation
3. Makes this information searchable for future retrieval
4. When a new message comes in, searches for related past conversations
5. Uses related memories to enhance AI responses

## Using Enhanced Memory Features

### Basic Usage

Enhanced memory is enabled by default in the `chat_manager.send_message` method:

```python
# Normal chat with memory enhancement
response = chat_manager.send_message(
    client_type="ocean",
    user_input="Tell me about that poem you wrote about the ocean"
)
```

### Explicit Memory Usage

For more control over memory usage, you can use `send_message_with_memory`:

```python
# Get the memory-enhanced response with explicit memory information
result = chat_manager.send_message_with_memory(
    client_type="vampire",
    user_input="Tell me more about Count Heathcliff"
)

# Access the response and memory information
response = result["response"]
memories_used = result["memories_used"]

# Print which memories were used
for memory in memories_used:
    print(f"Used memory: {memory['summary']}")
```

### Searching for Related Conversations

You can directly search for conversations by topic:

```python
# Find conversations about the ocean
ocean_convos = redis_client.search_conversations_by_topic("ocean")

# Find conversations related to a user input
related = redis_client.get_related_conversations(
    "I miss walking on the beach at sunset"
)
```

### Memory Management

You can manage the memory system:

```python
# Move conversations to long-term memory
redis_client.move_to_long_term_memory(chat_id)

# Clean up old conversations
removed_count = redis_client.cleanup_conversations(max_age_days=30)
```

## Redis Installation Options

### Standard Redis

The memory features work with the standard Redis installation, with some limitations:

```bash
# Install Redis server
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
```

### Redis Stack (Advanced Features)

For advanced features (vector search, JSON support), install Redis Stack:

```bash
# Using Docker
docker run -p 6379:6379 redis/redis-stack:latest
```

Or add the Redis Stack repository:

```bash
# Add repository
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

# Install Redis Stack
sudo apt update
sudo apt install redis-stack-server
```

## Demo Application

You can run the demo script to see how the memory features work:

```bash
python basic_memory_demo.py
```

The demo shows:
- Storing conversations with metadata
- Searching by topic
- Using memory to enhance responses
- Managing short-term and long-term memory

## Implementation Details

The memory system uses Redis data structures:
- **String keys** for storing conversations
- **Hash tables** for storing metadata 
- **Sets** for topic indexing
- **Sorted sets** for time-based retrieval

## Future Enhancements

1. **Vector Embeddings** - Using sentence transformers for semantic search
2. **AI-based Metadata** - Using Claude or other AI services to extract richer metadata
3. **Memory Summaries** - Creating and storing summaries of longer conversations
4. **User-specific Memory** - Personalizing memory retrieval per user
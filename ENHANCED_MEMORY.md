# Enhanced Conversational Memory

This document explains the enhanced memory features implemented in Ocean Chat, inspired by the memory_palace experiment.

## Overview

The enhanced memory system provides:

1. **Semantic memory** - Store and retrieve conversations based on content similarity
2. **Metadata extraction** - Automatically extract topics, sentiment, and key entities
3. **Memory management** - Organize conversations into short-term and long-term memory
4. **Contextual responses** - Enhance chat responses with relevant past conversations

## Architecture

The enhanced memory system uses Redis as a foundation with these key components:

### 1. Memory Storage

Conversations are stored in Redis with:
- **Conversation content** - The raw chat log
- **Metadata** - Topics, sentiment, summary, etc.
- **Search indexes** - For efficient retrieval by content and metadata

### 2. Memory Types

Conversations are organized into:
- **Short-term memory** (recent conversations)
- **Long-term memory** (older, processed conversations)

### 3. Memory Retrieval

Several methods are available for retrieving memories:
- Search by topic/keyword
- Find related conversations to user input
- Retrieve by time period

## Key Features

### Topic Extraction

The system extracts topics from conversations using:
- Keyword matching (simple implementation)
- More advanced processing possible with Claude or Mistral

### Memory-Enhanced Responses

When responding to users, the system:
1. Analyzes user input
2. Searches for relevant memories
3. Includes memory context in the model's prompt
4. Returns enriched responses with historical context

### Memory Management

The system maintains memory health by:
- Moving older conversations to long-term memory
- Periodically cleaning up outdated memories

## Implementation Details

### Redis Schema

The system uses these Redis data structures:
- **Hash** for storing conversation content
- **Sorted sets** for time-based organization
- **RedisJSON** for storing structured metadata
- **RediSearch** for advanced search capabilities

### Key Redis Commands

- `ZADD` - Add to time-ordered sets
- `ZREM` - Remove from sets
- `JSON.SET` - Store structured metadata
- `FT.SEARCH` - Search by content and metadata

## Usage Examples

### Storing with Metadata

```python
chat_id = redis_client.store_conversation_with_metadata(
    chat_type="ocean",
    conversation=chat_log,
    user_id="user123"
)
```

### Finding Related Conversations

```python
related = redis_client.get_related_conversations(
    "Tell me about the beach"
)
```

### Memory-Enhanced Chat

```python
response = chat_manager.send_message_with_memory(
    client_type="ocean",
    user_input="What was that poem about the waves?"
)
```

## Future Improvements

Possible enhancements include:

1. **Embedding-based retrieval** - Use vector embeddings for more accurate semantic search
2. **Adaptive memory prioritization** - Learn which memories are most useful based on user interactions
3. **Cross-conversation memory** - Allow memories to be shared across different chat types
4. **Memory consolidation** - Periodically summarize and compress old memories
5. **Sentiment-aware retrieval** - Match the emotional tone of memories with current conversation

## Testing the Enhanced Memory

Run the memory demo to see the enhanced features in action:

```bash
python memory_demo.py
```

The demo shows:
- Creating and storing conversations with metadata
- Searching for conversations by topic
- Retrieving related conversations
- Using memory to enhance chat responses
- Managing short-term and long-term memory
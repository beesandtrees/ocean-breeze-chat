# Enhanced Conversational Memory

This document explains the enhanced memory features implemented in Ocean Chat, inspired by the memory_palace experiment.

## Overview

The enhanced memory system provides:

1. **Semantic memory** - Store and retrieve conversations based on content similarity
2. **Metadata extraction** - Automatically extract topics, sentiment, and key entities
3. **Memory management** - Organize conversations into short-term and long-term memory
4. **Contextual responses** - Enhance chat responses with relevant past conversations

## Architecture

The enhanced memory system uses SQLite as a foundation with these key components:

### 1. Memory Storage

Conversations are stored in SQLite with:
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

### SQLite Schema

The system uses these SQLite tables:
- **conversations** for storing conversation content and metadata
- **chat_types** for organizing conversations by type
- **metadata** for storing structured metadata
- **search_index** for efficient content search

### Key SQLite Operations

- `INSERT` - Add new conversations
- `UPDATE` - Modify existing conversations
- `SELECT` - Retrieve conversations and metadata
- `DELETE` - Remove outdated conversations

## Usage Examples

### Storing with Metadata

```python
chat_id = db.store_conversation(
    chat_type="ocean",
    conversation=chat_log,
    user_id="user123",
    metadata={
        "topics": ["beach", "poetry"],
        "summary": "Discussion about coastal life",
        "sentiment": "positive"
    }
)
```

### Finding Related Conversations

```python
related = db.get_related_conversations(
    "Tell me about the beach",
    limit=5
)
```

### Memory-Enhanced Chat

```python
response = chat_manager.send_message(
    "ocean",
    user_input,
    max_tokens=1024,
    temperature=0.75
)
```

## Memory Tiers

The system implements a tiered memory approach:

1. **Immediate Memory**
   - Most recent conversations (last 2)
   - Full conversation context
   - Used for immediate continuity

2. **Recent Memory**
   - Last 5 conversations
   - Detailed summaries
   - Used for short-term context

3. **Long-term Memory**
   - Last 10 conversations
   - Brief mentions
   - Used for topic relevance

## Memory Integration

The memory system is integrated into the chat flow:

1. **Input Processing**
   - Analyze user input for memory triggers
   - Extract key topics and entities
   - Search for relevant memories

2. **Context Building**
   - Combine immediate context with relevant memories
   - Format memory context naturally
   - Include in system prompt

3. **Response Generation**
   - Generate response with memory context
   - Update conversation history
   - Extract and store new metadata

## Future Enhancements

Planned improvements include:

1. **Advanced Topic Extraction**
   - Use Claude for better topic identification
   - Implement hierarchical topic structure
   - Add topic relationships

2. **Memory Compression**
   - Implement better summarization
   - Add memory importance scoring
   - Optimize storage usage

3. **Enhanced Search**
   - Add semantic search capabilities
   - Implement fuzzy matching
   - Add time-based filtering

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
import redis
import time
from redis.commands.search.field import TextField, TagField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

# Connect to Redis
r = redis.Redis(host='redis', port=6379, decode_responses=True)


def create_schema():
    try:
        # Check if the index exists by attempting to get its info
        r.ft("idx:chats").info()
        print("Index 'idx:chats' already exists. Skipping schema creation.")
    except redis.exceptions.ResponseError:
        # Define your Redis schema for chat logs
        schema = (
            TextField("$.chat", as_name="chat"),
            TagField("$.user_id", as_name="user_id"),
            TextField("$.summary", as_name="summary"),
            TextField("$.sentiment", as_name="sentiment"),
            NumericField("$.word_count", as_name="word_count"),
            TagField("$.topics[*]", as_name="topics"),
            TagField("$.key_entities[*]", as_name="key_entities"),
            NumericField("$.timestamp", as_name="timestamp")
        )

        # Create an index for the chat logs
        r.ft("idx:chats").create_index(
            schema,
            definition=IndexDefinition(
                prefix=["chat:"], index_type=IndexType.JSON
            )
        )
        print("Index 'idx:chats' created successfully.")


def wait_for_redis():
    for _ in range(10):  # Retry 10 times
        try:
            r.ping()
            return True
        except redis.exceptions.ConnectionError:
            print("Waiting for Redis...")
            time.sleep(3)
    return False


# Run the schema creation function if Redis is available
if wait_for_redis():
    create_schema()
else:
    print("Could not connect to Redis. Exiting.")

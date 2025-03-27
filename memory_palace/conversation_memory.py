import uuid
from datetime import datetime
from sentence_transformers import SentenceTransformer
import numpy as np
from config import get_aws_session

aws_session = get_aws_session()


class ConversationMemory:
    def __init__(self):
        # Initialize AWS and embedding resources
        self.dynamodb = aws_session.resource('dynamodb')
        self.table = self.dynamodb.Table('ConversationMemory')

        # Use a lightweight, efficient embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def store_conversation(self, user_id, messages):
        # Generate a unique conversation ID
        conversation_id = str(uuid.uuid4())

        # Create a single text representation of the conversation
        full_text = " ".join(messages)

        # Generate embedding
        embedding = self.embedding_model.encode(full_text).tolist()

        # Store in DynamoDB
        item = {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'messages': messages,
            'embedding': embedding
        }

        self.table.put_item(Item=item)
        return conversation_id

    def find_similar_conversations(self, query, top_k=3):
        # Generate embedding for the query
        query_embedding = self.embedding_model.encode(query).tolist()

        # This is a placeholder for vector similarity search
        # In practice, you'd use a more sophisticated method
        # like cosine similarity or approximate nearest neighbors

        # Scan conversations (note: this is inefficient for large datasets)
        response = self.table.scan()

        # Calculate similarity (cosine similarity)
        similarities = []
        for item in response.get('Items', []):
            stored_embedding = item.get('embedding', [])
            similarity = self.cosine_similarity(query_embedding, stored_embedding)
            similarities.append((item, similarity))

        # Sort by similarity and return top k
        similar_conversations = sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]

        return similar_conversations

    def cosine_similarity(self, vec1, vec2):
        # Simple cosine similarity calculation
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


# Example usage
if __name__ == '__main__':
    memory = ConversationMemory()

    # Store a conversation about Proust
    proust_convo_id = memory.store_conversation(
        user_id='user123',
        messages=[
            "I love Marcel Proust's writing style in In Search of Lost Time.",
            "The way he describes memory is so intricate and beautiful."
        ]
    )

    # Later, find similar conversations
    similar_convos = memory.find_similar_conversations("Tell me about our Proust discussion")

    for convo, similarity in similar_convos:
        print(f"Similarity: {similarity}")
        print("Messages:", convo['messages'])

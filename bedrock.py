import boto3
import json


def generate_metadata_with_mistral(text):
    try:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")

        prompt = f"""
        Extract the following metadata from the given text:
        1. Top 5 most significant topics
        2. Overall theme
        3. Estimated complexity level
        4. Key entities or names mentioned
        
        Text:
        {text}
        
        Respond in a clear, structured JSON format.
        """

        request = json.dumps({
            "prompt": prompt,
            "max_tokens": 300,
            "temperature": 0.5
        })

        response = client.invoke_model(
            modelId="mistral.mistral-small-2402-v1:0",
            body=request
        )

        model_response = json.loads(response["body"].read().decode('utf-8'))

        return model_response['outputs'][0]['text']

    except Exception as e:
        print(f"Metadata generation error: {e}")
        return None


def analyze_conversation(conversation, analysis_type='full'):
    if analysis_type == 'full':
        conversation_text = " ".join([
            f"{msg['role']}: {msg['content']}" for msg in conversation
        ])
    elif analysis_type == 'user':
        conversation_text = " ".join([
            msg['content'] for msg in conversation if msg['role'] == 'user'
        ])
    elif analysis_type == 'assistant':
        conversation_text = " ".join([
            msg['content'] for msg in conversation if msg['role'] == 'assistant'
        ])

    return generate_metadata_with_mistral(conversation_text)


if __name__ == '__main__':
    text = [
        {
            "role": "user",
            "content": "yeah i want to make a sort of \"memory\" for you. I know you don't really have a memory - think of it as an external memory. like how I can look back through my old texts to see a conversation with someone and know what we were talking about and maybe even what we talked about a year ago"
        },
        {
            "role": "assistant",
            "content": "That's a fascinating idea! An external memory system would be really useful for maintaining context and continuity across conversations. It could help track long-term interests, past discussions, and provide a way to reference previous interactions.\n\nSome potential components of such a system might include:\n- A searchable log of conversations\n- Ability to tag or categorize different conversations\n- Summaries of key topics discussed\n- Ability to recall specific details from past interactions\n\nFrom my perspective, this would be similar to how humans use journals, notes, or message histories to remember past conversations and contexts.\n\nWould you be thinking of this as a personal tool just for your interactions with me, or something more general that could be used across different AI interactions? And what specific features would you find most useful in such a memory system?"
        }
    ]
    print(analyze_conversation(text))

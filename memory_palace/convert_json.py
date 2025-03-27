import json
import traceback
from redis_utils import add_conversation_to_db


def main():
    try:
        # Load JSON file
        with open('./chat_logs/claude.json', 'r') as file:
            conversations = json.load(file)
            print(f"Total conversations to import: {len(conversations)}")

        successful_imports = 0
        failed_imports = 0

        for i, conversation in enumerate(conversations):
            print(f"\nProcessing conversation {i + 1}")
            if add_conversation_to_db(conversation, 'mkm'):
                successful_imports += 1
            else:
                failed_imports += 1

        print(f"\nImport Summary:")
        print(f"Total conversations: {len(conversations)}")
        print(f"Successful imports: {successful_imports}")
        print(f"Failed imports: {failed_imports}")

    except Exception as e:
        print("Error in main process:")
        print(traceback.format_exc())


if __name__ == '__main__':
    main()

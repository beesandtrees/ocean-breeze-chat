import boto3


def create_conversation_memory_table():
    # Create the DynamoDB client
    dynamodb = boto3.resource('dynamodb')

    # Define the table
    table = dynamodb.create_table(
        TableName='ConversationMemory',
        KeySchema=[
            {
                'AttributeName': 'conversation_id',
                'KeyType': 'HASH'  # Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'conversation_id',
                'AttributeType': 'S'  # String type
            },
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'  # String type
            }
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait until the table exists
    table.meta.client.get_waiter('table_exists').wait(TableName='ConversationMemory')
    print("Table created successfully!")


# Run the function
create_conversation_memory_table()

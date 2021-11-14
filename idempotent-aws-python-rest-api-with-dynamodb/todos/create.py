import json
import logging
import os
import time
import uuid

import boto3
from botocore.exceptions import ClientError


def create(event, context):
    data = json.loads(event['body'])
    if 'text' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't create the todo item.")

    timestamp = str(time.time())

    item = {
        'id': str(uuid.uuid1()),
        'text': data['text'],
        'checked': False,
        'createdAt': timestamp,
        'updatedAt': timestamp,
    }

    # write the todo to the database
    try:
        boto3.client('dynamodb').transact_write_items(TransactItems=[{
            'Update': {
                'TableName': os.environ['DYNAMODB_TABLE'],
                'Key': {
                    'id': {'S': item['id']},
                },
                'UpdateExpression': 'SET #todo = :todo, #createdAt = :createdAt, #updatedAt = :updatedAt',
                'ExpressionAttributeNames': {
                    '#todo': 'text',
                    '#createdAt': 'createdAt',
                    '#updatedAt': 'updatedAt',
                },
                'ExpressionAttributeValues': {
                    ':todo': {'S': item['text']},
                    ':createdAt': {'S': item['createdAt']},
                    ':updatedAt': {'S': item['updatedAt']},
                },
            }
        }], ClientRequestToken=context.aws_request_id)
    except ClientError as e:
        # Duplicate request, simply ignore
        logging.error(e)

    # create a response
    response = {
        "statusCode": 200,
        "body": json.dumps(item)
    }

    return response

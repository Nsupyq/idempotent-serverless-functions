import json
import logging
import uuid

from todos.todo_model import TodoModel
from pynamodb.transactions import TransactWrite
from pynamodb.connection import Connection
from pynamodb.exceptions import TransactWriteError

def create(event, context):
    print(event['body'])
    data = json.loads(event['body'])
    if 'text' not in data:
        logging.error('Validation Failed')
        return {'statusCode': 422,
                'body': json.dumps({'error_message': 'Couldn\'t create the todo item.'})}

    if not data['text']:
        logging.error('Validation Failed - text was empty. %s', data)
        return {'statusCode': 422,
                'body': json.dumps({'error_message': 'Couldn\'t create the todo item. As text was empty.'})}

    a_todo = TodoModel(todo_id=str(uuid.uuid1()),
                       text=data['text'],
                       checked=False)
                       
    # write the todo to the database using transaction
    connection = Connection()
    try:
        with TransactWrite(client_request_token=context.aws_request_id,connection=connection) as transact_write:
            transact_write.save(a_todo)
    except TransactWriteError as e:
        logging.error(e) # this error indicates that the operation has been finished, so we can simply return

    # create a response
    return {'statusCode': 201,
            'body': json.dumps(dict(a_todo))}


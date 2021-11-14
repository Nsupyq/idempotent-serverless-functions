<!--
title: 'GraphQL query endpoint in NodeJS on AWS with DynamoDB and Idempotence Guaranteed'
description: 'A single-module GraphQL endpoint with query and mutation functionality, ensuring idempotence.'
layout: Doc
framework: v1
platform: AWS
language: nodeJS
priority: 1
authorLink: 'https://github.com/gismoranas'
authorName: 'Gismo Ranas'
authorAvatar: 'https://avatars0.githubusercontent.com/u/5903107?v=4&s=140'
-->

# GraphQL query endpoint in NodeJS on AWS with DynamoDB and Idempotence Guarantee

This example demonstrates how to ensure idempotence in a GraphQL service with the Serverless Framework, targeting AWS.
It is based on the example of [GraphQL API with DynamoDB](../aws-node-graphql-api-with-dynamodb/README.md).

## How to guarantee idempotence

The side effect of the function is writing the nickname.
AWS DynamoDB provides an [idempotent transactional write API](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TransactWriteItems.html), which  writes name for only once and does nothing on retry.
It needs an argument `clientRequestToken` to check whether the current transactional write is a retry.
The `clientRequestToken` should be a universally unique identifier.
Then we use [`awsRequestId`](https://docs.aws.amazon.com/lambda/latest/dg/nodejs-context.html) to be the `clientRequestToken`.
This is a unique identifier provided by AWS Lambda.
When Lambda retries a function, it will use the same `awsRequestId` as that in the first invocation.

## Usage

Start by initializing a project and installing the [graphql](https://www.npmjs.com/package/graphql) module.
```sh
$ npm init
$ npm install --save graphql
```

Now we can use it in `handler.js`, where we declare a schema and then use it to serve query requests.
```js
/* handler.js */
const {
  graphql,
  GraphQLSchema,
  GraphQLObjectType,
  GraphQLString,
  GraphQLNonNull
} = require('graphql')

// This method just inserts the user's first name into the greeting message.
const getGreeting = firstName => `Hello, ${firstName}.`

// Here we declare the schema and resolvers for the query
const schema = new GraphQLSchema({
  query: new GraphQLObjectType({
    name: 'RootQueryType', // an arbitrary name
    fields: {
      // the query has a field called 'greeting'
      greeting: {
        // we need to know the user's name to greet them
        args: { firstName: { name: 'firstName', type: new GraphQLNonNull(GraphQLString) } },
        // the greeting message is a string
        type: GraphQLString,
        // resolve to a greeting message
        resolve: (parent, args) => getGreeting(args.firstName)
      }
    }
  }),
})

// We want to make a GET request with ?query=<graphql query>
// The event properties are specific to AWS. Other providers will differ.
module.exports.query = (event, context, callback) => graphql(schema, event.queryStringParameters.query)
  .then(
    result => callback(null, {statusCode: 200, body: JSON.stringify(result)}),
    err => callback(err)
  )
```

Pretty simple! To deploy it, define a service in `serverless.yml`, and set the handler to service HTTP requests.
```yml
# serverless.yml
service: graphql-api

functions:
  query:
    handler: handler.query
    events:
      - http:
          path: query
          method: get
```
Now we can bring it to life:
```sh
$ serverless deploy
# Serverless: Packaging service...
# Serverless: Excluding development dependencies...
# Serverless: Uploading CloudFormation file to S3...
# Serverless: Uploading artifacts...
# Serverless: Uploading service .zip file to S3 (357.34 KB)...
# Serverless: Validating template...
# Serverless: Updating Stack...
# Serverless: Checking Stack update progress...
# ..............
# Serverless: Stack update finished...
# Service Information
# service: graphql-api
# stage: dev
# region: us-east-1
# stack: graphql-api-dev
# api keys:
#   None
# endpoints:
#   GET - https://9qdmq5nvql.execute-api.us-east-1.amazonaws.com/dev/query
# functions:
#   query: graphql-api-dev-query

$ curl -G 'https://9qdmq5nvql.execute-api.us-east-1.amazonaws.com/dev/query' --data-urlencode 'query={greeting(firstName: "Jeremy")}'
# {"data":{"greeting":"Hello, Jeremy."}}
```

In the real world, virtually any service that does something valuable has a data store behind it. For example, suppose users have nicknames that should appear in the greeting message. We need a database to store the nicknames, and we can expand our GraphQL API to update them.

Let's start by adding a database to the resource definitions in `serverless.yml`. We need a table keyed on the user's first name, which we define using CloudFormation, as well as some provider configuration to allow our function to access it.
```yml
# add to serverless.yml

provider:
  name: aws
  runtime: nodejs6.10
  environment:
    DYNAMODB_TABLE: ${self:service}-${self:provider.stage}
  iamRoleStatements:
    - Effect: Allow
      Action:
        - dynamodb:GetItem
        - dynamodb:UpdateItem
      Resource: "arn:aws:dynamodb:${opt:region, self:provider.region}:*:table/${self:provider.environment.DYNAMODB_TABLE}"

resources:
  Resources:
    NicknamesTable:
      Type: 'AWS::DynamoDB::Table'
      Properties:
        AttributeDefinitions:
          - AttributeName: firstName
            AttributeType: S
        KeySchema:
          - AttributeName: firstName
            KeyType: HASH
        ProvisionedThroughput:
          ReadCapacityUnits: 1
          WriteCapacityUnits: 1
        TableName: ${self:provider.environment.DYNAMODB_TABLE}
```

We need to run `serverless deploy` again to update the changes made in `serverless.yml`:

```
$ serverless deploy
```

To use it we need the [aws-sdk](https://www.npmjs.com/package/aws-sdk), In this example, I use the SDK's vanilla DocumentClient to access DynamoDB records.
```sh
$ npm install --save aws-sdk
```

Include these in our handler, and then we can get to work.
```js
// add to handler.js
const AWS = require('aws-sdk');
const dynamoDb = new AWS.DynamoDB.DocumentClient();
```

Before, we defined a method that just returned a string value for the greeting message. However, the GraphQL library can also use Promises as resolvers. Since the DocumentClient uses a callback pattern, we'll wrap these in promises and use the DynamoDB `get` method to check the database for a nickname for the user.

```js
// add to handler.js
const promisify = foo => new Promise((resolve, reject) => {
  foo((error, result) => {
    if(error) {
      reject(error)
    } else {
      resolve(result)
    }
  })
})

// replace previous implementation of getGreeting
const getGreeting = firstName => promisify(callback =>
  dynamoDb.get({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { firstName },
  }, callback))
  .then(result => {
    if(!result.Item) {
      return firstName
    }
    return result.Item.nickname
  })
  .then(name => `Hello, ${name}.`)

  // add method for updates
const changeNickname = (firstName, nickname) => promisify(callback =>
  dynamoDb.update({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { firstName },
    UpdateExpression: 'SET nickname = :nickname',
    ExpressionAttributeValues: {
      ':nickname': nickname
    }
  }, callback))
  .then(() => nickname)
```

You can see here that we added a method `changeNickname`, but the GraphQL API is not yet using it. We need to declare a mutation that the front-end can use to perform updates. We previously only added a `query` declaration to the schema. Now we need a `mutation` as well.

```js
// alter schema
const schema = new GraphQLSchema({
  query: new GraphQLObjectType({
    /* unchanged */
  }),
  mutation: new GraphQLObjectType({
    name: 'RootMutationType', // an arbitrary name
    fields: {
      changeNickname: {
        args: {
          // we need the user's first name as well as a preferred nickname
          firstName: { name: 'firstName', type: new GraphQLNonNull(GraphQLString) },
          nickname: { name: 'nickname', type: new GraphQLNonNull(GraphQLString) }
        },
        type: GraphQLString,
        // update the nickname
        resolve: (parent, args) => changeNickname(args.firstName, args.nickname)
      }
    }
  })
})
```

After these changes, we can make the greeting request again and receive the same result as before.
```sh
$ curl -G 'https://9qdmq5nvql.execute-api.us-east-1.amazonaws.com/dev/query' --data-urlencode 'query={greeting(firstName: "Jeremy")}'
# {"data":{"greeting":"Hello, Jeremy."}}
```
But if I want the API to call me "Jer", I can update the nickname for "Jeremy".
```sh
$ curl -G 'https://9qdmq5nvql.execute-api.us-east-1.amazonaws.com/dev/query' --data-urlencode 'query=mutation {changeNickname(firstName:
 \"Jeremy\", nickname: \"Jer\")}'
$ curl -G 'https://9qdmq5nvql.execute-api.us-east-1.amazonaws.com/dev/query' --data-urlencode 'query={greeting(firstName: \"Jeremy\")}'
# {"data":{"greeting":"Hello, Jer."}}
```

The API will now call anyone named "Jeremy" by the nickname "Jer". This kind of separation of concerns lets you build front-ends and services that offload logic into back-ends that use abstract data access and processing behind one, strongly typed, validated, uniform contract that comes with rich versioning and deprecation strategies.

To deploy this service yourself, download the [source code](#todo) and deploy it with the Serverless Framework. Happy building!

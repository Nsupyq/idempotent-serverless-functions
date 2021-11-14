# idempotent-serverless-functions
Examples of idempotent serverless functions

This repository demonstrates how to ensure the idempotence of serverless functions, which run on AWS Lambda using the traditional Serverless Framework.
Our examples are based on the examples in the repository [Serverless Examples](https://github.com/serverless/examples).
We add idempotence to the original functions.

## What is idempotence

Idempotence means multiple invocations of a function have the same side-effect as one invocation.

## Why we need idempotence

AWS Lambda uses retry to perform fault tolerance.
When your function fails because of out of memory or some other reasons, it will be directly retried until it finishes successfully.
For serverless functions with side-effect, retry may cause data inconsistency.
For example, retrying a function purchasing a product may cause multiple deduction of money.
Therefore, AWS Lambda requires programmers to write [idempotent function](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-function-idempotent/).

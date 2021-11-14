<!--
title: 'Node.js AWS Lambda connecting to MongoDB Atlas'
description: 'Shows how to connect AWS Lambda to MongoDB Atlas.'
layout: Doc
framework: v1
platform: AWS
language: nodeJS
priority: 10
authorLink: 'https://github.com/welkie'
authorName: 'Matt Welke'
authorAvatar: 'https://avatars0.githubusercontent.com/u/7719209'
-->
# aws-node-mongodb-atlas with idempotence guarantee

An example idempotent app, based on this [blog post](https://mattwelke.com/2019/02/18/free-tier-serverless-mongodb-with-aws-lambda-and-mongodb-atlas.html), showing how to connect AWS Lambda to MongoDB Atlas, which must be configured with a user with read/write privileges and an IP whitelist to allow Lambda to connect to it. See blog post for detailed walkthrough setting up MongoDB Atlas.

## How to guarantee idempotence

The side effect is inserting the new pet. We make the function idempotent by using the [`awsRequestId`](https://docs.aws.amazon.com/lambda/latest/dg/nodejs-context.html) provided by AWS Lambda to be `_id`. Then the function will insert only one new pet even if pets.insertOne(newPet) is retried.

# shortlink-api

A serverless link shortener: **Lambda + API Gateway + DynamoDB**, deployed entirely from the command line with Claude Code. No servers, no framework — one Python file.

## Endpoints

```
POST /links          {"url": "https://long.example/..."}  → {"short": "https://.../Ab3xYz"}
GET  /{code}         301 redirect to the original URL (and counts the hit)
GET  /stats/{code}   {"url": ..., "hits": 42, "created": ...}
```

Try it:

```bash
curl -X POST https://lq913p2t40.execute-api.us-east-1.amazonaws.com/links \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com"}'
```

## How it works

- **API Gateway (HTTP API)** routes requests to a single **Lambda** (`lambda_function.py`, Python 3.13)
- **DynamoDB** stores `{code, url, hits, created}`; codes are 6 random base62 chars with a conditional-write collision guard
- IAM role is scoped to exactly three actions on one table

Built as Activity 2 of a Claude Code × AWS course — directed in plain English, executed by AI, understood by me.

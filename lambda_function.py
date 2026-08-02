import json
import secrets
import string
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

table = boto3.resource("dynamodb").Table("shortlinks")

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6


def _response(status, body, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    return {"statusCode": status, "headers": h, "body": json.dumps(body)}


def _create_link(event):
    try:
        payload = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "body must be JSON"})

    url = payload.get("url", "")
    if not url.startswith(("http://", "https://")) or len(url) > 2048:
        return _response(400, {"error": "send {\"url\": \"https://...\"}"})

    for _ in range(5):
        code = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
        try:
            table.put_item(
                Item={
                    "code": code,
                    "url": url,
                    "hits": 0,
                    "created": datetime.now(timezone.utc).isoformat(),
                },
                ConditionExpression="attribute_not_exists(code)",
            )
            break
        except ClientError as e:
            if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
    else:
        return _response(500, {"error": "could not allocate a code, try again"})

    domain = event["requestContext"]["domainName"]
    return _response(201, {"code": code, "short": f"https://{domain}/{code}", "url": url})


def _redirect(code):
    item = table.get_item(Key={"code": code}).get("Item")
    if not item:
        return _response(404, {"error": f"no link for code {code}"})
    table.update_item(
        Key={"code": code},
        UpdateExpression="ADD hits :one",
        ExpressionAttributeValues={":one": 1},
    )
    return {"statusCode": 301, "headers": {"Location": item["url"]}}


def _stats(code):
    item = table.get_item(Key={"code": code}).get("Item")
    if not item:
        return _response(404, {"error": f"no link for code {code}"})
    return _response(
        200,
        {"code": code, "url": item["url"], "hits": int(item["hits"]), "created": item["created"]},
    )


def lambda_handler(event, context):
    route = event.get("routeKey", "")
    params = event.get("pathParameters") or {}
    if route == "POST /links":
        return _create_link(event)
    if route == "GET /stats/{code}":
        return _stats(params.get("code", ""))
    if route == "GET /{code}":
        return _redirect(params.get("code", ""))
    return _response(404, {"error": "not found"})

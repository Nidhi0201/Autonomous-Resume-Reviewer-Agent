"""
Netlify Function for /health endpoint.
"""
import json


def handler(event, context):
    """
    Health check endpoint.
    """
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"status": "ok"}),
    }

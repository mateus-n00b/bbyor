from .challenge import handle_challenge, handle_result, handle_request
from .baseline import handle_baseline_challenge, handle_baseline_result
import json

functions = {
    "challenge": handle_challenge,
    "fhe_result": handle_result,
    "received": None,
    "request_challenge": handle_request,
    "baseline_challenge": handle_baseline_challenge,
    "baseline_result": handle_baseline_result,
}

def handle_messages(body):
    content = body['content']
    print(type(content), body['content'][0:50])
    if 'type' in content:
        content = json.loads(content)
        tp = content["type"]
        functions[tp](body, content)
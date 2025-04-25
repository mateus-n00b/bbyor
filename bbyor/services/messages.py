from .challenge import handle_challenge, handle_result
import json 
functions = {
    "challenge": handle_challenge,
    "fhe_result": handle_result,
    "received": None
} 

def handle_messages(body):
    content = body['content']  
    print(type(content), body['content'][0:50])
    # content = json.loads(content)
    if 'type' in content:  
        content = json.loads(content)      
        tp = content["type"]
        # proccess msg
        functions[tp](body, content)
from .challenge import handle_challenge

functions = {
    "challenge": handle_challenge,
    "fhe_result": None
} 

def handle_messages(content):  
    tp = content["type"]
    # proccess msg
    functions[tp](content)
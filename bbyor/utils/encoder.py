import json
import ast
def string_to_integer(s: str) -> int:
    return int.from_bytes(s.encode(), 'big') 

def decode_hex(values):
    decoded_values = [int(x, 16) for x in values]
    return decoded_values

def integer_to_string(i: int) -> str:
    byte_length = (i.bit_length() + 7) // 8  # calculate how many bytes needed
    return i.to_bytes(byte_length, 'big').decode()

def hex_to_int(x):
    if isinstance(x, str):
        return int(x, 16)
    elif isinstance(x, list):
        return [hex_to_int(i) for i in x]
    else:
        return x


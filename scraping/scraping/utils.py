import hashlib


def list_to_string(list):
    tmp = ''.join(list)
    tmp = tmp.replace('\n', '')
    return tmp

def string_to_id(input_string, id_size=10):
    hash_object = hashlib.sha256(input_string.encode())
    hex_digest = hash_object.hexdigest()
    numeric_id = int(hex_digest, 16)
    final_id = str(numeric_id)[-id_size:]
    return final_id
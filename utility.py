import secp256k1
import hashlib
FAMILY = "wallet"

def generate_keys():
    key_handler = secp256k1.PrivateKey()
    print("Public Key", key_handler.pubkey.serialize().hex())
    print("Private Key", key_handler.private_key.hex())
    return key_handler.pubkey.serialize().hex(), key_handler.private_key.hex()

def get_wallet_address(public_key):
    return hashlib.sha512(FAMILY.encode('utf-8')).hexdigest()[0:6] + \
           hashlib.sha512(public_key.encode('utf-8')).hexdigest()[0:64]


if __name__ == "__main__":
    generate_keys()
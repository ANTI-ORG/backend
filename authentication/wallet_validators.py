import base64

import base58
import eth_account
from eth_account.messages import encode_defunct
from nacl import signing
from nacl.exceptions import BadSignatureError


def validate_ethereum_wallet(web3_address: str, nonce: str, signature: str):
    try:
        recovered_address = eth_account.Account.recover_message(encode_defunct(text=nonce),
                                                                signature=bytes.fromhex(signature[2:]))
        if recovered_address.lower() != web3_address.lower():
            return False
    except Exception:
        return False

    return True


def validate_solana_wallet(web3_address: str, nonce: str, signature: str):
    try:
        public_key_bytes = base58.b58decode(web3_address)
        verify_key = signing.VerifyKey(public_key_bytes)
        verify_key.verify(nonce.encode(), base64_to_bytes(signature))
        return True
    except BadSignatureError:
        print('Invalid signature.')
        return False
    except Exception as e:
        print('Error while solana wallet validation')
        return False


def base64_to_bytes(base64_str: str) -> bytes:
    return base64.b64decode(base64_str)

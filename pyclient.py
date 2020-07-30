import base64
import yaml
import requests
import hashlib
import random
from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchList
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch
from utility import get_wallet_address

FAMILY_NAME = 'wallet'

class Client:
    def __init__(self, private_key):
        self._baseUrl = "http://localhost:8008"
        privateKey = Secp256k1PrivateKey.from_hex(private_key)
        self._signer = CryptoFactory(create_context('secp256k1')) \
            .new_signer(privateKey)
        self._publicKey = self._signer.get_public_key().as_hex()
        self._address = get_wallet_address(self._publicKey)

    def deposit(self, amount):
        return self._wrap_and_send("deposit", amount)

    def withdraw(self, amount):
        return self._wrap_and_send( "withdraw",  amount)

    def transfer(self, amount, clientToKey):
        return self._wrap_and_send("transfer", amount, clientToKey)

    def balance(self):
        result = self._send_to_restapi(
            "state/{}".format(self._address))
        try:
            return base64.b64decode(yaml.safe_load(result)["data"])
        except BaseException:
            return None

    def _send_to_restapi(self, suffix, data=None, contentType=None):
        if self._baseUrl.startswith("http://"):
            url = "{}/{}".format(self._baseUrl, suffix)
        else:
            url = "http://{}/{}".format(self._baseUrl, suffix)
        headers = {}
        if contentType is not None:
            headers['Content-Type'] = contentType
        try:
            if data is not None:
                result = requests.post(url, headers=headers, data=data)
            else:
                result = requests.get(url, headers=headers)

            if not result.ok:
                raise Exception("Error {}: {}".format(
                    result.status_code, result.reason))
        except requests.ConnectionError as err:
            raise Exception(
                'Failed to connect to {}: {}'.format(url, str(err)))
        except BaseException as err:
            raise Exception(err)
        return result.text

    def _wrap_and_send(self,  *values):
        payload = ",".join(values)
        print(" Payload ")
        print(payload)
        # Construct the address where we'll store our state
        address = self._address
        inputAddressList = [address]
        outputAddressList = [address]

        if "transfer" == values[0]:
            toAddress = get_wallet_address(values[2])
            inputAddressList.append(toAddress)
            outputAddressList.append(toAddress)
            print("Inside the block")


        # Create a TransactionHeader
        header = TransactionHeader(
            signer_public_key=self._publicKey,
            family_name=FAMILY_NAME,
            family_version="1.0",
            inputs=inputAddressList,
            outputs=outputAddressList,
            dependencies=[],
            payload_sha512=hashlib.sha512(payload.encode()).hexdigest(),
            batcher_public_key=self._publicKey,
            nonce=random.random().hex().encode()
        ).SerializeToString()

        # Create a Transaction from the header and payload above
        transaction = Transaction(
            header=header,
            payload=payload.encode(),
            header_signature=self._signer.sign(header)
        )

        transactionList = [transaction]

        # Create a BatchHeader from transactionList above
        header = BatchHeader(
            signer_public_key=self._publicKey,
            transaction_ids=[txn.header_signature for txn in transactionList]
        ).SerializeToString()

        # Create Batch using the BatchHeader and transactionList above
        batch = Batch(
            header=header,
            transactions=transactionList,
            header_signature=self._signer.sign(header))

        # Create a Batch List from Batch above
        batch_list = BatchList(batches=[batch])
        batch_id = batch_list.batches[0].header_signature
        print(batch_id)

        # Send batch_list to rest-api
        return self._send_to_restapi(
            "batches",
            batch_list.SerializeToString(),
            'application/octet-stream')


if __name__ == "__main__":    
    key1 = "5107755972e4ac15fe53374236828d33130445ff0ae59cb6392d1cf71af393d3"
    key2 = "864e3502a9b29f4113a43cacffa400f70e3b93cd5b3c31dc3d345630fba96799"
    public_key_2 ="0290afad77549247e05c0b766cbec7e7a6ce53973ae03d00d3de410b48c3a1acc1"
    cli1 = Client(key2)
    # cli1.transfer("800", public_key_2)
    print(cli1.balance())



    
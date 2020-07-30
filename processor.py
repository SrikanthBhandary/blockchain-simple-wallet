import sys
import traceback
import hashlib

# Importing the things from sawtooth
from sawtooth_sdk.processor.core import TransactionProcessor
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.handler import TransactionHandler
from utility import get_wallet_address
import constants


FAMILY = "wallet"
SW_NAME_SPACE = hashlib.sha512(FAMILY.encode('utf-8')).hexdigest()[0:6]


class WalletHandler(TransactionHandler):
    def __init__(self, namespace):
        self.namespace = namespace
        self.wallet_address = ""

    @property
    def family_name(self):
        """
        family_name should return the name of the transaction family that this
        handler can process, e.g. "intkey"
        """
        return FAMILY

    @property
    def family_versions(self):
        """
        family_versions should return a list of versions this transaction
        family handler can process, e.g. ["1.0"]
        """
        return ["1.0"]

    @property
    def namespaces(self):
        """
        namespaces should return a list containing all the handler's
        namespaces, e.g. ["abcdef"]
        """
        return [self.namespace]

    def apply(self, transaction, context):
        header = transaction.header
        payload = transaction.payload.decode('utf-8').split(',')
        operation = payload[0]
        amount = int(payload[1])
        sender = header.signer_public_key
        print("*" * 50)
        print(sender)
        self.wallet_address = get_wallet_address(sender)

        if operation == constants.DEPOSIT:
            self.deposit(context, amount)
        elif operation == constants.WITHDRAW:
            self.withdraw(context, amount)
        elif operation == constants.TRANSFER:
            if(len(payload) == 3):
                receiver = payload[2]
            self.transfer(context, amount, receiver)
        else:
            print("Invalid operation")

    def deposit(self, context, amount):
        print("Reached")
        print(self.wallet_address)
        current_entry = context.get_state([self.wallet_address])
        if current_entry:
            balance = int(current_entry[0].data)
            new_balance = int(amount) + int(balance)
        else:
            new_balance = int(amount)
        state_data = str(new_balance).encode('utf-8')
        print("Tests")
        addresses = context.set_state({self.wallet_address: state_data})
        if len(addresses) < 1:
            raise InvalidTransaction("State Error")

    def withdraw(self, context, amount):
        current_entry = context.get_state([self.wallet_address])
        new_balance = 0
        if current_entry:
            balance = int(current_entry[0].data)
            if(balance > amount):
                raise InvalidTransaction('Not enough money. The amount ' +
                                         'should be lesser or equal to {} '.format(balance))
            else:
                new_balance = int(balance) - int(amount)
        else:
            print('No user with the key {} '.format(self.wallet_address))
        state_data = str(new_balance).encode('utf-8')
        addresses = context.set_state(
            {self.wallet_address: state_data})

        if len(addresses) < 1:
            raise InvalidTransaction("State Error")


    def transfer(self, context, amount, receiver):
        if amount <= 0:
            raise InvalidTransaction("The amount cannot be <= 0")
        receiver_address = get_wallet_address(receiver)
        sender_ledger = context.get_state([self.wallet_address])
        receiver_ledger = context.get_state([receiver_address])

        if len(sender_ledger) == 0:
            raise InvalidTransaction('No user (debtor) with the key {} '.format(self.wallet_address))

        if len(receiver_ledger) == 0:
            raise InvalidTransaction('No user (creditor) with the key {} '.format(receiver_address))

        balance = int(sender_ledger[0].data)
        balance_to = int(receiver_ledger[0].data)
        if balance < amount:
            raise InvalidTransaction('Not enough money. ' +
                                     'The amount should be less or equal to {} '.format(balance))
        else:
            print("Debiting balance with {}".format(amount))
            update_sender_balance = balance - int(amount)
            state_data = str(update_sender_balance).encode('utf-8')
            context.set_state({self.wallet_address: state_data})
            update_beneficiary_balance = balance_to + int(amount)
            state_data = str(update_beneficiary_balance).encode('utf-8')
            context.set_state({receiver_address: state_data})

def main():
    try:
        processor = TransactionProcessor(url='tcp://localhost:4004')
        handler = WalletHandler(SW_NAME_SPACE)
        processor.add_handler(handler)
        processor.start()
    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()











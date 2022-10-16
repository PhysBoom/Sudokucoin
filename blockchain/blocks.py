import base64
import time
from hashlib import sha256
from blockchain.wallet.elliptic_curve import EllipticCurvePoint
from merkletools import MerkleTools


class Input:
    __slots__ = (
        "prev_tx_hash",
        "output_index",
        "signature",
        "_hash",
        "address",
        "index",
        "amount",
    )

    def __init__(self, prev_tx_hash, output_index, address, index=0, signature=None):
        self.prev_tx_hash = prev_tx_hash
        self.output_index = output_index
        self.address = address
        self.index = 0
        self._hash = None
        self.signature = signature.encode() if type(signature) == str else signature
        self.amount = None

    def __repr__(self):
        return f"Input({self.prev_tx_hash}, {self.output_index}, {self.address}, {self.index}, {self.signature})"

    def sign(self, wallet):
        hash_string = "{}{}{}{}".format(
            self.prev_tx_hash, self.output_index, self.address, self.index
        ).encode()
        self.signature = base64.b64encode(wallet.sign(hash_string))

    @property
    def hash(self):
        if self._hash:
            return self._hash
        if not self.signature and self.prev_tx_hash != "COINBASE":
            raise Exception("Sign the input first")
        hash_string = f"{self.prev_tx_hash}{self.output_index}{self.address}{self.signature.encode() if type(self.signature) == str else self.signature}{self.index}"
        self._hash = sha256(
            sha256(hash_string.encode()).hexdigest().encode("utf8")
        ).hexdigest()
        return self._hash

    @property
    def as_dict(self):
        return {
            "prev_tx_hash": self.prev_tx_hash,
            "output_index": self.output_index,
            "address": str(self.address),
            "index": self.index,
            "hash": self.hash,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data):
        inst = cls(
            data["prev_tx_hash"],
            data["output_index"],
            data["address"],
            data["index"],
        )
        inst.signature = data["signature"]
        inst._hash = None
        return inst


class Output:
    __slots__ = "_hash", "address", "index", "amount", "input_hash"

    def __init__(self, address, amount, index=0, input_hash=None):
        self.address = address
        self.index = 0
        self.amount = round(float(amount), 7)
        # i use input hash here to make output hash unique, especialy for COINBASE tx
        self.input_hash = input_hash
        self._hash = None

    def __repr__(self):
        return f"Output(address={self.address}, amount={self.amount}, index={self.index}, input_hash={self.input_hash})"

    @property
    def hash(self):
        if self._hash:
            return self._hash

        hash_string = f"{self.amount}{self.index}{self.address}{self.input_hash}"
        self._hash = sha256(
            sha256(hash_string.encode()).hexdigest().encode("utf8")
        ).hexdigest()
        return self._hash

    @property
    def as_dict(self):
        return {
            "amount": round(float(self.amount), 7),
            "address": str(self.address),
            "index": self.index,
            "input_hash": self.input_hash,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data):
        inst = cls(
            data["address"],
            data["amount"],
            data["index"],
        )
        inst.input_hash = data["input_hash"]
        inst._hash = None
        return inst


class Tx:
    __slots__ = "inputs", "outputs", "timestamp", "_hash"

    def __init__(self, inputs, outputs, timestamp=None):
        self.inputs = inputs
        self.outputs = outputs
        self.timestamp = timestamp or int(time.time())
        self._hash = None

    def __repr__(self):
        return f"Tx(inputs={self.inputs}, outputs={self.outputs}, timestamp={self.timestamp})"

    @property
    def hash(self):
        if self._hash:
            return self._hash

        # calculating input_hash for outputs
        inp_hash = sha256(
            (str([el.as_dict for el in self.inputs]) + str(self.timestamp)).encode()
        ).hexdigest()
        for el in self.outputs:
            el.input_hash = inp_hash

        hash_string = f'{[el.hash for el in self.inputs]}{[f"{el.amount}{el.address}{el.index}" for el in self.outputs]}{self.timestamp}'

        self._hash = sha256(
            sha256(hash_string.encode()).hexdigest().encode("utf8")
        ).hexdigest()
        return self._hash

    @property
    def as_dict(self):
        inp_hash = sha256(
            (str([el.as_dict for el in self.inputs]) + str(self.timestamp)).encode()
        ).hexdigest()
        for el in self.outputs:
            el.input_hash = inp_hash
        return {
            "inputs": [el.as_dict for el in self.inputs],
            "outputs": [el.as_dict for el in self.outputs],
            "timestamp": self.timestamp,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data):
        inps = [Input.from_dict(el) for el in data["inputs"]]
        outs = [Output.from_dict(el) for el in data["outputs"]]
        inp_hash = sha256(
            (str([el.as_dict for el in inps]) + str(data["timestamp"])).encode()
        ).hexdigest()
        for el in outs:
            el.input_hash = inp_hash

        inst = cls(
            inps,
            outs,
            data["timestamp"],
        )
        inst._hash = None
        return inst


class Block:

    __slots__ = (
        "prev_hash",
        "index",
        "txs",
        "timestamp",
        "merkel_root",
        "puzzle_solution",
    )

    def __init__(
        self, txs, index, prev_hash, timestamp=None, puzzle_solution=0, merkel_root=None
    ):
        self.txs = txs or []
        self.prev_hash = prev_hash
        self.index = index
        self.puzzle_solution = puzzle_solution
        self.timestamp = timestamp or int(time.time())
        self.merkel_root = merkel_root

    def __repr__(self):
        return "Block(index={}, prev_hash={}, timestamp={}, merkel_root={}, puzzle_solution={}, txs={})".format(
            self.index,
            self.prev_hash,
            self.timestamp,
            self.merkel_root,
            self.puzzle_solution,
            self.txs,
        )

    def build_merkel_tree(self):
        """
        Merkel Tree used to hash all the transactions, and on mining do not recompute Txs hash everytime
        Which making things much faster.
        And tree used because we can append new Txs and rebuild root hash much faster, when just building
        block before mine it.
        """
        if self.merkel_root:
            return self.merkel_root
        mt = MerkleTools(hash_type="SHA256")
        for el in self.txs:
            mt.add_leaf(el.hash)
        mt.make_tree()
        self.merkel_root = mt.get_merkle_root()
        return self.merkel_root

    def hash(self, solution=None):
        if solution:
            self.puzzle_solution = solution
        block_string = "{}{}{}{}{}".format(
            self.build_merkel_tree(),
            self.prev_hash,
            self.index,
            self.puzzle_solution,
            self.timestamp,
        )
        return sha256(
            sha256(block_string.encode()).hexdigest().encode("utf8")
        ).hexdigest()

    @property
    def winning_address(self):
        return (
            self.txs[0].outputs[0].address
            if self.txs and self.txs[0].inputs[0].prev_tx_hash == "COINBASE"
            else None
        )

    @property
    def seed(self):
        seed_string = "{}{}{}{}".format(
            self.build_merkel_tree(), self.prev_hash, self.index, self.timestamp
        )
        return sha256(seed_string.encode()).hexdigest()

    @property
    def as_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "hash": self.hash(),
            "txs": [el.as_dict for el in self.txs],
            "puzzle_solution": self.puzzle_solution,
            "merkel_root": self.merkel_root,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            [Tx.from_dict(el) for el in data["txs"]],
            data["index"],
            data["prev_hash"],
            data.get("timestamp"),
            data.get("puzzle_solution"),
            data.get("merkel_root"),
        )

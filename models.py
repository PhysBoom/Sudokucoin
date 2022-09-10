
from typing import List
from pydantic import BaseModel, Field

from blockchain.blocks import Tx, Block

"""
Just some Input models for FastApi
"""

class InputModel(BaseModel):
    prev_tx_hash:str
    output_index:int
    address:str
    index:int
    signature:str

class OutputModel(BaseModel):
    amount:int
    address:str
    index:int
    input_hash:str

class TxModel(BaseModel):
    inputs:List[InputModel]
    outputs:List[OutputModel]
    timestamp:int
    class Config:
        arbitrary_types_allowed = True

    def to_tx(self):
        return Tx(
            self.inputs,
            self.outputs,
            self.timestamp
        )

class BlockModel(BaseModel):
    index:int
    puzzle_solution:str
    timestamp:int
    prev_hash:str
    txs:List[TxModel]
    class Config:
        arbitrary_types_allowed = True

    def to_block(self):
        return Block(
            [tx.to_tx() for tx in self.txs],
            self.index,
            self.prev_hash,
            self.timestamp,
            self.puzzle_solution
        )

class BlocksModel(BaseModel):
    blocks:List[BlockModel]
    class Config:
        arbitrary_types_allowed = True

class NodesModel(BaseModel):
    nodes:List[str]
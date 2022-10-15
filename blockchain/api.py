from blockchain.blockchain import Blockchain
from blockchain.db import DB
from .blocks import Tx, Block
from .wallet.address import Address
from websocket_server import BlockchainEvent, WebsocketServer

class API:

    """
        Some wrapper around blockchain to add some logic without changing
        main blockchain code
    """

    def __init__(self, blockchain):
        self.bc = blockchain
        self.ws = WebsocketServer(8765)
        self.ws.start()

    def reset_chain(self):
        self.bc = Blockchain(DB(), Address.create())

    def get_user_balance(self, address):
        return sum(self.bc.db.unspent_outputs_amount[str(address)].values())

    def get_user_unspent_txs(self, address):
        res = []
        for tx_hash,out_hash in self.bc.db.unspent_txs_by_user_hash[str(address)]:
            amount = self.bc.db.unspent_outputs_amount[str(address)][out_hash]
            res.extend({"tx": tx_hash, "output_index": index, "out_hash": out_hash, "amount": amount} for index, out in enumerate(self.bc.db.transaction_by_hash[tx_hash]['outputs']) if out['hash'] == out_hash)

        return res

    def get_chain(self, from_block:int, limit:int=20):
        res = [b.as_dict for b in self.bc.chain[from_block:from_block+limit]]
        # adding blocks from splitbrain
        if len(res) < limit:
            res += self.bc.fork_blocks.values()
        return res

    def get_block_currently_mining(self, private_key: int):
        wallet = Address(private_key)
        block = self.bc.force_block(wallet)
        puzzle = self.bc.to_puzzle(block)
        return {"puzzle": puzzle, "block": block.as_dict}

    def add_block(self, block):
        block = Block.from_dict(block)
        res = self.bc.add_block(block)
        if res:
            self.bc.rollover_block(block)
        return res

    async def mine_block(self, block: Block):
        # Reset the chain if there are more than 10000 blocks
        if len(self.bc.chain) > 10000:
            self.bc = Blockchain()
            await self.ws.broadcast(BlockchainEvent(event_type="reset", message="The blockchain has been reset!", data={}), {})

        else: 
            res = self.bc.mine_block(block)
            if res:
                await self.ws.broadcast(BlockchainEvent(
                    event_type="block_mined",
                    message=f"User {block.winning_address} mined block {block.index}",
                    data={}
                ))
            return res

    def add_tx(self, tx):
        return self.bc.add_tx(Tx.from_dict(tx))

    def get_head(self):
        return self.bc.head.as_dict if self.bc.head else {}
            
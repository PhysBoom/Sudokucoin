import base64

import rsa
import binascii

from sudoku.sudoku_board import SudokuBoard
from sudoku.sudoku_gen import SudokuGenerator
from .wallet.address import Address
from .wallet.elliptic_curve import EllipticCurvePoint


class TxVerifier:
    def __init__(self, db):
        self.db = db

    def verify(self, inputs, outputs):
        total_amount_in = 0
        total_amount_out = 0
        for i,inp in enumerate(inputs):
            if inp.prev_tx_hash == 'COINBASE' and i == 0:
                total_amount_in = int(self.db.config['mining_reward'])
                continue
 
            try:
                out = self.db.transaction_by_hash[inp.prev_tx_hash]['outputs'][inp.output_index]
            except KeyError:
                raise Exception('Transaction output not found.')

            total_amount_in += int(out['amount'])

            if (inp.prev_tx_hash,out['hash']) not in self.db.unspent_txs_by_user_hash.get(out['address'], set()):
                raise Exception('Output of transaction already spent.')

            hash_string = '{}{}{}{}'.format(
                inp.prev_tx_hash, inp.output_index, inp.address, inp.index
            )
            try:
                Address.verify(hash_string.encode(), binascii.unhexlify(base64.b64decode(inp.signature)), EllipticCurvePoint.decode(inp.address))
            except:
                raise Exception('Signature verification failed: %s' % inp.as_dict)

        for out in outputs:
            total_amount_out += int(out.amount)

        if total_amount_in < total_amount_out:
            raise Exception('Insuficient funds.')

        return total_amount_in - total_amount_out

class BlockOutOfChain(Exception):
    pass

class BlockVerificationFailed(Exception):
    pass

class BlockVerifier:
    def __init__(self, db):
        self.db = db
        self.tv = TxVerifier(db)

    def verify(self, head, block):
        total_block_reward = int(self.db.config['mining_reward'])

        # verifying block solution
        # Our deterministic thing for sudoku generation is using the set difficulty + the prev hash of the block as the seed.
        s = SudokuGenerator(self.db.config['difficulty'], block.seed)
        if not s.generate_board().is_valid_solution(SudokuBoard.decode(block.puzzle_solution)):
            raise BlockVerificationFailed('Invalid puzzle solution')

        # verifying transactions in a block
        for tx in block.txs[1:]:
            fee = self.tv.verify(tx.inputs, tx.outputs)
            total_block_reward += fee
        
        total_reward_out = 0
        for out in block.txs[0].outputs:
            total_reward_out += out.amount

        # verifying block reward
        if total_block_reward != total_reward_out:
            raise BlockVerificationFailed('Wrong reward sum')
        
        # verifying some other things
        if head:
            if head.index >= block.index:
                raise BlockOutOfChain('Block index number wrong')
            if head.hash() != block.prev_hash:
                raise BlockOutOfChain('New block not pointed to the head')
            if head.timestamp > block.timestamp:
                raise BlockOutOfChain('Block from the past')

        return True

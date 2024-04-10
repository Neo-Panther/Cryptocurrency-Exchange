from typing import Any, TypedDict
from collections.abc import Iterable
import datetime
import json
import hashlib
import rsa
import hmac
import os

class Request(TypedDict):
  id: int
  amount: int

class customEncoder(json.JSONEncoder):
  def default(self, o: Any) -> Any:
    if isinstance(o, set):
      return list(o)
    elif isinstance(o, Transaction):
      return o.__dict__
    elif isinstance(o, datetime):
      return o.strftime("%d|%m|%Y><%H:%M:%S")
    elif isinstance(o, rsa.PublicKey):
      return "PublicKey(" + str(o.n) + ', ' + str(o.e) + ')'
    elif isinstance(o, rsa.PrivateKey):
      return "__private key object"
    elif isinstance(o, bytes):
      return "__signature bytes object"
    return super().default(o)

class Transaction():
  def __init__(self, from_id: int, to_id: int, amount: int, sender_sign: bytes) -> None:
    self.from_id = from_id
    self.to_id = to_id
    self.amount = amount
    self.timestamp = datetime.now()
    self.transaction_id = from_id^to_id^amount
    self.sender_sign: bytes = sender_sign
  
  def  __str__(self):
    return json.dumps(self.__dict__, cls=customEncoder, indent=4, separators=(',', ': '))

class Block():
  def __init__(self, prev_hash: str, height: int, transactions: Iterable[Transaction], miner_id: int, difficulty: int) -> None:
    self.previous_hash = prev_hash
    self.difficulty = difficulty
    self.nonce = 0
    self.height = height
    self.miner_id = miner_id
    self.timestamp = datetime.now()
    self.header_hash = Blockchain.calculateHash(prev_hash + str(height) + str(miner_id) + self.timestamp.strftime("%d|%m|%Y><%H:%M:%S") + str(difficulty) + str(self.nonce))
    self.transactions:list[Transaction] = list(transactions)
    
  def __str__(self) -> str:
    return json.dumps(self.__dict__, cls=customEncoder, indent=4, separators=(',', ': '))

class User():
  def __init__(self, init_amt: int, id: int) -> None:
    self.amount = init_amt
    self.id = id
    # to_id => (amount, hkey)
    self.requests_sent: dict[int, tuple[int, bytes]] = dict()
    # from_id => (amount, hkey)
    self.requests_received: dict[int, tuple[int, bytes]] = dict()
    self.hkey = os.urandom(16)  # secret key of the user
    self.public_key, self.__private_key = rsa.newkeys(512)

  def sign(self, data: Any) -> bytes:
    data = str(data)
    return rsa.sign(data.encode('utf-8'), self.__private_key, 'SHA-1')

  @staticmethod
  def verifySig(message: Any, signature: bytes, key: rsa.PublicKey) -> bool:
    return rsa.verify(str(message).encode('utf-8'), signature, key) == 'SHA-1'

  @staticmethod
  def generateChallengeH() -> bytes:
    return os.urandom(15)
  
  def createResponseH(self, request_to_id: int, challenge: bytes, bit: bytes) -> bytes:
    t = bytearray(challenge)
    t.append(bytearray(bit)[0])
    return hmac.new(self.requests_sent[request_to_id][1], bytes(t), hashlib.sha256).digest()
  
  @staticmethod
  def verifyResponseH(key: bytes, challenge: bytes, bit: bytes, response: bytes) -> bool:
    t = bytearray(challenge)
    t.append(bytearray(bit)[0])
    r2 = hmac.new(key, bytes(t), hashlib.sha256).digest()
    return r2 == response

class Blockchain():
  def __init__(self) -> None:
    # pool of all active nodes
    self.difficulty = 1
    self.parent_user = User(10000, 0)
    self.current_active_users: dict[int, User] = dict()
    self.current_active_users[0] = self.parent_user
    # header_hash => block
    self.blockchain: dict[str, Block] = dict()
    genesis_block = Blockchain.createBlock(self.calculateHash(''), 0, [], 0, 0)
    self.blockchain[genesis_block.header_hash] = genesis_block
    self.unmined_transactions: list[Transaction] = []
    self.newest_block = genesis_block.header_hash
  
  @staticmethod
  def createBlock(prev_hash: str, height: int, transactions: Iterable[Transaction], miner_id: int, difficulty: int) -> Block:
    return Block(prev_hash, height, transactions, miner_id, difficulty)

  def viewUser(self, user_id: int) -> None:
    if user_id in self.current_active_users:
      print("Printing user info for user id:", user_id)
      usr = self.current_active_users[user_id]
      print("User has crypto amount:", usr.amount)
      print("User pending requests sent", usr.requests_sent)
      print("User pending requests received", usr.requests_received)
      print("User public key", usr.public_key)
    else:
      print("No such User")

  def getSentRequestStatus(self, request_to_id: int) -> None:
    if self.parent_user.id in self.current_active_users[request_to_id].requests_received:
      print("Request has been delivered, pending approval by the other party")
    else:
      for txn in self.unmined_transactions:
        if txn.to_id == self.parent_user.id and txn.from_id == request_to_id:
          print("Request has been approved, wait for mining and validation")
          return
    print("No such request is pending, it may have already been executed.\nNew request can be sent")

  def mineBlock(self) -> None:
    print("Mining started\n")
    block_txn = self.unmined_transactions
    # verify all unmined transactions
    for txn in block_txn.copy():
      if not self.verifyTransaction(txn):
        block_txn.remove(txn)
    # if there are no transactions, stop mining
    if not block_txn:
      self.unmined_transactions.clear()
      return print("No valid transactions for this block found")

    print("Valid transactions separated:", block_txn)
    new_block = Block(self.newest_block, len(self.blockchain), block_txn, self.parent_user.id, self.difficulty)

    def count0start(s: str) -> int:
      ans = 0
      for i in s:
        if i != "0": return ans
        ans += 1
      return ans

    while count0start(self.calculateHash(new_block)) < self.difficulty:
      new_block.nonce += 1

    if not self.validateBlock(new_block):
      print("Block failed verification for 50% validators, applying penalty to the miner")
      self.parent_user.amount -= 1
    else:    
      print("Block Mined, 2 confirmations received, applying valid transaction operations::")
      for transaction in new_block.transactions:
        # perform the transaction operations
        self.current_active_users[transaction.from_id].amount -= transaction.amount
        self.current_active_users[transaction.to_id].amount += transaction.amount

      print('Rewarding the Miner')
      self.parent_user.amount += 1
      # Block is valid, make necessary changes to the blockchain
      self.unmined_transactions.clear()
      self.blockchain[new_block.header_hash]=new_block
      self.newest_block=new_block.header_hash
      if len(self.blockchain) >= 10:
        self.difficulty += 1

  def verifyTransaction(self, transaction:Transaction) -> bool:
    if User.verifySig(transaction.transaction_id, transaction.sender_sign, self.current_active_users[transaction.from_id].public_key):
      print("Sender's signature verified")
      if transaction.amount >= self.current_active_users[transaction.from_id].amount:
        print('Sender\'s funds verified')
        return True
      else:
        # Sender does not hacve the requested goods
        print("User id:", transaction.from_id, " does not have enough funds")
    return False
  
  def validateBlock(self, block: Block) -> bool:
    # check the previous hash and the block height
    if not (block.previous_hash in self.blockchain) or not (self.blockchain[block.previous_hash].height==block.height-1):
      print("Block previous hash is invalid")
      return False
    
    print('previous hash verified')
    # check the headerhash
    header_hash=self.calculateHash(block.previous_hash + str(block.height) + str(block.miner_id) + block.timestamp.strftime("%d|%m|%Y><%H:%M:%S") + str(block.difficulty) + str(block.nonce))
    if not header_hash==block.header_hash:
      return False

    if(header_hash[:self.difficulty] != "0"*block.difficulty):
      print("PoW conditions not met")
      return False

    print('header hash and PoW verified')
    print('block verified')
    # block verified
    return True

  def send_crypto(self, to_id: int, amount: int) -> None:
    new_txn = Transaction(self.parent_user.id, to_id, amount, self.parent_user.sign(self.parent_user.id^to_id^amount))
    self.unmined_transactions.append(new_txn)

  def getReceivedRequests(self) -> list[Request]:
    return [{"id": i[0], "amount": i[1][0]} for i in self.parent_user.requests_received.items()]

  def getPendingSentRequests(self) -> list[Request]:
    return [{"id": i[0], "amount": i[1][0]} for i in self.parent_user.requests_sent.items()]
  
  def acceptRequest(self, request_from_id: int) -> None:
    if request_from_id in self.parent_user.requests_received:
      # challenge from sending user
      challenge = User.generateChallengeH()
      # random bit
      bit = os.urandom(1)
      # response creation by sender
      resp = self.current_active_users[request_from_id].createResponseH(self.parent_user.id, challenge, bit)
      # verify using key
      User.verifyResponseH(self.parent_user.requests_received[request_from_id][1], challenge, bit, resp)
      print("User verified through Challenge-Response Authentication")
      self.current_active_users[request_from_id].requests_sent.pop(self.parent_user.id)
      self.send_crypto(request_from_id, self.parent_user.requests_received.pop(request_from_id)[0])
    else:
      print("No such pending request")
  
  def rejectRequest(self, request_from_id: int) -> None:
    if request_from_id in self.parent_user.requests_received:
      self.parent_user.requests_received.pop(request_from_id)
      self.current_active_users[request_from_id].requests_sent.pop(self.parent_user.id)
    else:
      print("No such pending request")
  
  def sendRequest(self, request_to_id: int, amount: int) -> None:
    if request_to_id not in self.parent_user.requests_sent:
      self.parent_user.requests_sent[request_to_id] = (amount, self.parent_user.hkey)
      self.current_active_users[request_to_id].requests_received[self.parent_user.id] = (amount, self.parent_user.hkey)
      self.parent_user.hkey = os.urandom(16)
    else:
      print("New request can be sent to a user only if the previous request has been responded to")

  def deleteRequest(self, request_to_id: int) -> None:
    if request_to_id in self.parent_user.requests_sent:
      self.parent_user.requests_sent.pop(request_to_id)
      self.current_active_users[request_to_id].requests_received.pop(self.parent_user.id)
    else:
      print("No such pending request")

  @staticmethod
  def calculateHash(s: Any) -> str:
    return hashlib.sha256(str(s).encode('utf-8')).hexdigest()
  
  def addUser(self, id: int, initial_amount: int) -> None:
    self.current_active_users[id] = User(initial_amount, id)

  def changeParentUser(self, id: int) -> None:
    self.parent_user = self.current_active_users[id]

  def showBlockchain(self) -> None:
    print("###  Printing Blocks in the Blockchain  ###")
    cur_block = self.blockchain[self.newest_block]
    while cur_block.height != 0:
      print(cur_block)
      cur_block = self.blockchain[cur_block.previous_hash]
    # print genesis block
    return print(cur_block)

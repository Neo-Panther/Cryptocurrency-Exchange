from blockchain import *
def getInt(prompt: str) -> int:
  while(True):
    try:
      i = int(input(prompt))
      break
    except ValueError:
      print("Input not an integer, please enter again")
  return i

print("Creating Blockchain")
# manufacturer's stock
print("Creating First User with id", 0, "with amount:", 10000)
bc = Blockchain(User(10000, 0))
print("Blockchain Created")

def addUser(init_amt: int, id: int) -> None:
  bc.current_active_users[id] = User(init_amt, id)

print("Adding some dummy Users")
addUser(500, 1)
addUser(600, 2)
addUser(0, 3)

print("Adding some dummy Transactions")
bc.unmined_transactions.append(Transaction(1, 2, 100, bc.current_active_users[1].sign(1^2^100)))

print("Adding some dummy Requests")
bc.changeParentUser(1)
bc.sendRequest(0, 1000)
bc.changeParentUser(0)

### Add any code here to test the blockchain


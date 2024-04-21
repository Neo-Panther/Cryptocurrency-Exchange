import time
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

print("Beginning Main Loop")
wait = 3
while(True):
  for i in range(wait, -1, -1):
    print("\rMoving ahead in", i, end = '\r')
    time.sleep(1)
  print('-'*100, end = '\n\n')

  print("Current User:", bc.parent_user.id)

  print("::::::::Option Menu::::::::")
  print("Add New User: 1")
  print("Change Current User: 2")
  print("Send Cryptocurrency: 3")
  print("Get Sent Request Status: 4")
  print("Display blockchain: 5")
  print("Mine Block: 6")
  print("Display Users: 7")
  print("Display User with id: 8")
  print("Send Request: 9")
  print("Display Active Sent Requests(", len(bc.parent_user.requests_sent), "pending): 10")
  print("Display Received Requests (", len(bc.parent_user.requests_received), "pending): 11")
  print("Confirm a Received Request: 12")
  print("Reject a Received Request: 13")
  print("Delete Sent Request: 14")
  print("End Connection with Blockchain: 15")

  selection = getInt("Choose an Operation to Perform: ")
  print()

  if selection == 1:
    id = getInt("Enter Id: ")
    inuse = id in bc.current_active_users
    while inuse:
      print("id:", inuse, "already in use, please enter unique id")
      id = getInt("Enter Id: ")
      inuse = id in bc.current_active_users
    
    init_amt = getInt("Enter Initial Amount: ")
    addUser(init_amt, id)
    print("User successfully created")
    print("User public info broadcasted to all nodes")
    wait = 3
 
  elif selection == 2:
    id = getInt("Enter the User id to Change to (Enter -1 or an Invalid id to Stop): ")
    if id not in bc.current_active_users:
      print("id not Found on the Network, Stopping")
      continue
    bc.parent_user = bc.current_active_users[id]
    print("User changed")
    wait = 1

  elif selection == 3:
    receiver_id = getInt("Enter the Receiver's id: ")
    if receiver_id not in bc.current_active_users:
      print("id not Found on the Network, Stopping")
      continue
    print("Your current amount:", bc.parent_user.amount)
    amt = getInt("Enter amount to send (Enter invalid amount to stop): ")
    if amt <= 0 or amt > bc.parent_user.amount:
      print("Invalid amount, Stopping")
      continue
    bc.send_crypto(receiver_id, amt)
    wait = 3

  elif selection == 4:
    receiver_id = getInt("Enter the request reciever's id: ")
    bc.getSentRequestStatus(receiver_id)
    wait = 2

  elif selection == 5:
    bc.showBlockchain()
    wait = 5

  elif selection == 6:
    bc.mineBlock()
    wait = 5

  elif selection == 7:
    print("::Parent User Info (with private key)::")
    print(bc.parent_user)
    print("::Successful Transactions against the user::")
    block = bc.blockchain[bc.newest_block]
    while block.height != 0:
      for txn in block.transactions:
        if txn.from_id == bc.parent_user.id or txn.to_id == bc.parent_user.id:
            print(txn)
            print()
      block = bc.blockchain[block.previous_hash]
    print("\nOther Nodes' data available with parent::")
    for i in bc.current_active_users.keys():
      if i != bc.parent_user.id:
        print("-"*100)
        us = bc.current_active_users[i] 
        print("User id:", us.id)
        print("User Amount:", us.amount)
        print("User Public Key:", us.public_key)
        print("::Successful Transactions against the user::")
        block = bc.blockchain[bc.newest_block]
        while block.height != 0:
          for txn in block.transactions:
            if txn.from_id == us.id or txn.to_id == us.id:
                print(txn)
                print("-"*50)
          block = bc.blockchain[block.previous_hash]
    wait = 5

  elif selection == 8:
    id = getInt("Enter the User id to get info of (Enter -1 or an Invalid id to Stop): ")
    if id not in bc.current_active_users:
      print("id not Found on the Network, Stopping")
      continue
    
    us = bc.current_active_users[id] 
    if id == bc.parent_user.id:
      print(us)
    else:
      print("User id:", us.id)
      print("User Amount:", us.amount)
      print("User Public Key:", us.public_key)
    print("::Successful Transactions against the user::")
    block = bc.blockchain[bc.newest_block]
    while block.height != 0:
      for txn in block.transactions:
        if txn.from_id == us.id or txn.to_id == us.id:
            print(txn)
            print("-"*50)
      block = bc.blockchain[block.previous_hash]

  elif selection == 9:
    receiver_id = getInt("Enter the request Receiver's id: ")
    if receiver_id not in bc.current_active_users:
      print("id not Found on the Network, Stopping")
      continue
    amt = getInt("Enter amount to request (Enter invalid amount to stop): ")
    if amt <= 0:
      print("Invalid amount, Stopping")
      continue
    bc.sendRequest(receiver_id, amt)
    wait = 3

  elif selection == 10:
    print("::Request Sent (to id, amount)::")
    for l in bc.getPendingSentRequests():
      print(l["id"], l["amount"])
    wait = 3

  elif selection == 11:
    print("::Request Received (from id, amount)::")
    for l in bc.getReceivedRequests():
      print(l["id"], l["amount"])
    wait = 3
  
  elif selection == 12:
    sender_id = getInt("Enter the id of the sender of the request: ")
    bc.acceptRequest(sender_id)
    wait = 3
  
  elif selection == 13:
    sender_id = getInt("Enter the id of the sender of the request: ")
    bc.rejectRequest(sender_id)
    wait = 1

  elif selection == 15:
    print("Closing connection to the Blockchain Network...")
    break

  elif selection == 14:
    receiver_id = getInt("Enter the id of the receiver of the request: ")
    bc.deleteRequest(receiver_id)
    wait = 1

  else:
    print("Incorrect input; please choose again")
    wait = 2
  
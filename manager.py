from flask import Flask, jsonify, request
import time
import os
import json
import uuid
from multiprocessing import Process, Queue
from pathlib import Path

from settings import CUSTOMERS

app = Flask(__name__)


def validate_customer(customer: str) -> bool:
    if customer in CUSTOMERS:
          return True
    return False

def custom_search(search_data, uuid):
    # Push UUID into inprogress table
    search_to_inprogress(uuid)
    print("SUBPROCESS")

    # Start sleep timer. This is where a search would normally happen
    # The sleep mimics time taken to do search
    time.sleep(30)

    # Move UUID from in progress to completed
    search_to_completed(uuid)

def search_to_inprogress(uuid):
    Path("{}".format(uuid)).touch()

def search_to_completed(uuid):
    with open("{}".format(uuid), "+a") as f:
        f.write("Done")

# Example of REST GET for retrieving a piece of data, in this case just from a file.
@app.route("/threats/<customer>/", methods=['GET'])
def Datamanager_Getthreat(customer):

    if validate_customer(customer) == True:
        # At this point a search should be instigated to retrieve the data from the DB or similar
        # For this example we will use a local file with some sample json
        with open("example.txt", "r") as f:
            ret_data = json.loads(f.read())
    else:
         # Invalid customer
         ret_data = {"status": "ERROR", "message": "Invalid Customer", "code": 403}
         
    return jsonify(ret_data)


# Example Customer REST API POST/GET/DELETE
@app.route("/customer/add", methods=['POST'])
def Datamanager_Customer_add():
    json = request.get_json()

    new_customer = json.get('customer')
    with open("customers.txt", "+a") as f:
        f.writelines("{}\n".format(new_customer))

    return jsonify({"status": "SUCCESS", "message": "Customer added", "code": 200})

@app.route("/customer/delete", methods=['DELETE'])
def Datamanager_Customer_remove():
    json = request.get_json()

    customer = json.get('customer')
    with open("customers.txt", "+r") as f:
        customers = f.readlines()
        f.seek(0)
        for cust in customers:
             if customer != cust.strip("\n"):
                  f.write("{}".format(cust))
        f.truncate()

    return jsonify({"status": "SUCCESS", "message": "Customer removed", "code": 200})

@app.route("/customers", methods = ['GET'])
def Datamanager_Customers():
    with open("customers.txt", "+r") as f:
        customers = f.readlines()

    return jsonify({"status": "SUCCESS", "message": customers, "code": 200})


# Rudimentary interface to start searches and get results
# Search is initiated by the create endpoint with async search mocked by the process call
# A touch file is created and only become non zero in size once the search time has completed.
@app.route("/search/<customer>/create", methods=['POST'])
def Datamanager_Customer_search(customer):
    json = request.get_json()

    search_args = json.get('search_args')

    if validate_customer(customer) == False:
        # Invalid customer
        return jsonify({"status": "ERROR", "message": "Invalid Customer", "code": 403})
    
    # Generate UUID
    new_uuid = str(uuid.uuid4())

    # Spawn task with UUID info
    p = Process(target=custom_search, args=(search_args, new_uuid))
    p.start()

    # return UUID to allow for poll for completion
    return jsonify({"status": "SUCCESS", "message": new_uuid, "code": 200})


@app.route("/search/<customer>/<uuid>", methods=['GET'])
def Datamanager_Get_search(customer, uuid):

    if validate_customer(customer) == False:
        # Invalid customer
        return jsonify({"status": "ERROR", "message": "Invalid Customer", "code": 403})

    # Id UUID in completed table
    if os.stat("{}".format(uuid)).st_size == 0:
        return jsonify({"status": "SUCCESS", "message": "False", "code": 200})
    return jsonify({"status": "SUCCESS", "message": "True", "code": 200})


if __name__ == "__main__":
	app.run(port=5000)


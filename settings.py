
CUSTOMERS = []


with open("customers.txt", "r") as f:
    for customer in f.readlines():
        CUSTOMERS.append(customer.strip("\n"))

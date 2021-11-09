import json
import requests

URI = "http://localhost:5000/bugs"
class Bug:
    def __init__(self, Title , Body )
        Bugid = None
        self.Title = Title
        self.Body = Body
      
        
def getData(id = None):
    
    try:
        reply = requests.get(URI)
    except requests.RequestException:
        print('Communication error')
    else:
        print(reply.json())
        #bugs = reply.json()
        
def getDataById():
    bugid = int(input("Enter bug id \n"))
    API_END_POINT = "URI" + "/" + str(bugid)
    try:
        reply = requests.get(API_END_POINT)
    except requests.RequestException:
        print('Communication error')
    else:
        print(reply.json())

def createBug_call(bug):
    
    API_END_POINT = "URI" + "/" 
    try:
        reply = requests.post(API_END_POINT)
    except requests.RequestException:
        print('Communication error')
    else:
        print(reply.json())

def createBug():
    

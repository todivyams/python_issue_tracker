from json_bug_server import app
import unittest
import requests
import json
token = None

class AppTest(unittest.TestCase):

    def test1_index(self):
        tester = app.test_client(self)
        response = tester.get('/')
        statuscode = response.status_code
        self.assertEqual(statuscode, 200)
        
        
    def test2_login(self):
        global token
        
        tester = app.test_client(self)
        response = tester.post('/login',auth=('admin1', 'passwd1'))
        statuscode = response.status_code
        self.assertEqual(statuscode, 200)
        token = response.json['token']
        #print(token)


    def test3_login(self):
        tester = app.test_client(self)
        response = tester.post('/login',auth=('abcdef', 'passwd1'))
        statuscode = response.status_code
        self.assertEqual(statuscode, 401)

    def test4_login(self):
        tester = app.test_client(self)
        response = tester.post('/login')
        statuscode = response.status_code
        self.assertEqual(statuscode, 401)

    def test5_registeruser(self):
        header = {'x-api-key':token}
        newuser = {"User Name": "user1",
                "Email": "user1.email.com",
                "Password": "passwd"}
        json_obj = json.dumps(newuser)
        
        tester = app.test_client(self)
        response = tester.post('/users',headers=header, json=newuser)
        statuscode = response.status_code
        self.assertEqual(statuscode, 200)

    def test9_listusers(self):
        tester = app.test_client(self)
        response = tester.get('/users')
        statuscode = response.status_code
        self.assertEqual(statuscode, 203)
        #print(response.get_json())

    def test10_listusers(self):
        header = {'x-api-key':token}
        tester = app.test_client(self)
        response = tester.get('/users',headers=header)
        statuscode = response.status_code
        self.assertEqual(statuscode, 200)
        #print(response.get_json())

    def test11_listuser(self):
        header = {'x-api-key':token}
        tester = app.test_client(self)
        response = tester.get('/users/100',headers=header)
        statuscode = response.status_code
        self.assertEqual(statuscode, 200)
        

    def test12_listuser(self):
        header = {'x-api-key':token}
        tester = app.test_client(self)
        response = tester.get('/users/1',headers=header)
        statuscode = response.status_code
        self.assertEqual(statuscode, 200)
        #print(response.get_json())

    
        


        
if __name__ == "__main__":
    unittest.main()

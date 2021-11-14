from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from waitress import serve
from datetime import datetime
from json import JSONEncoder
import os
import enum


app =Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20),unique = True, nullable = False)
    email = db.Column(db.String(100),unique = True, nullable = False)
    password = db.Column(db.String(60),nullable = False)
    comments = db.relationship('Comments',lazy=True)
    bugsassigned = db.relationship('Bugs',backref='assignedbugs',lazy=True)
    
    def __repr__(self):
        return "{'id':%d,'username':%s,'email':%s}"%(self.id,self.username,
                                                     self.email)

class Bugs(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100),nullable = False)
    description = db.Column(db.String(500),nullable=False)
    reportedon = db.Column(db.DateTime, nullable=False,default=datetime.utcnow)
    reportedby = db.Column(db.String(20),nullable = False)
    assignedto = db.Column(db.String(20),db.ForeignKey('users.username'),nullable = True)
    assignedby = db.Column(db.Integer,nullable = True)
    status = db.Column(db.String(20),nullable = False,default="open")
    comments = db.relationship('Comments',backref='bugcomments',lazy=True)
    
    def __repr__(self):
        record = {'id':self.id,'title':self.title,'description':self.description,
                  'reportedby':self.reportedby,'reportedon':self.reportedon,
                  'status':self.status,'comments':self.comments}
        
        return str(record)
      

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    bugid = db.Column(db.Integer,db.ForeignKey('bugs.id'),nullable = False)
    comment = db.Column(db.String(500),nullable=False)
    commentedon = db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    commentedby = db.Column(db.String(20),db.ForeignKey('users.username'),nullable=False)

    def __repr__(self):
        return "{'id':%d,'user':%s,'bugid':%d,'comment':%s}"%(self.id,
                                self.commentedby,self.bugid, self.comment)


if not os.path.isfile('./data.db'):
    print("creating the DB")
    db.create_all()
    db.session.commit()
else:
    print("DB already exsits")


def serialize_comment(bug):
    dict_comments =dict()
    for item in bug.comments:
        dict_comment ={'Comment':item.__dict__['comment'],'Commented By':item.__dict__['commentedby'],
                       'Commented Time':item.__dict__['commentedon']}
        dict_comments[item.__dict__['id']]= dict_comment
    return dict_comments

class Status(enum.Enum):
    Open = 1
    Assigned = 2
    Inprogress = 3
    Closed = 4
    Blocked = 5
    Resolved = 6
      
@app.route('/')
def index():
    return("Welcome to BugsWorld !!")


@app.route('/bugs')
def getbugs():
    print("REST API call for getting all bugs")
    bugs = Bugs.query.all()
    if bugs is None:
        return {"Bugs ": None}
    dict_bug_list = []
    for bug in bugs:
        dict_bug = {"Bug ID":bug.id,"Bug Title":bug.title,"Bug Description":bug.description,
                    "Reported By":bug.reportedby,"Reported Time":bug.reportedon,
                    "Bug Status":bug.status}
        dict_comments = serialize_comment(bug)
        dict_bug['comments']=dict_comments
        dict_bug_list.append(dict_bug)
    return jsonify(dict_bug_list)
       

@app.route('/bugs/<id>')
def getbug(id):
    print("REST API call for getting a specified bug")
    bug = Bugs.query.get(id)

    if bug is None:
        return {"No bug with id ": id}
    
    dict_bug = {"Bug ID":bug.id,"Bug Title":bug.title,"Bug Description":bug.description,
                "Reported By":bug.reportedby,"Reported Time":bug.reportedon,
                "Bug Status":bug.status}
    dict_comments = serialize_comment(bug)
    dict_bug['comments']=dict_comments
    print (dict_bug)

    return dict_bug


@app.route('/bugs',methods = ['POST'])
def createbug():
    
    bug = Bugs()
    print("REST API call for creating a new bug")
    bug.title = request.json['Bug Title']
    print("bug.title :",bug.title)
    bug.description = request.json['Bug Description']
    print("bug.description :",bug.description)
    bug.reportedby = request.json['Reported By']
    print("add bug")
    db.session.add(bug)
    db.session.commit()
    return {"successfully created bug":bug.id}

@app.route('/bugs/assign/<id>',methods = ['PUT'])
def assignbug(id):
    print("REST API call for updating a bug")
    bug = Bugs.query.get(id)
    if bug is None:
        return {"No bug with id ": id}
    bug.assignedto = request.json['Assigned To']
    bug.assignedby = request.json['Assigned By']

    db.session.add(bug)
    db.session.commit()
    return {f"Assigned bug {bug.id} ": f"to {bug.assignedto}"}

@app.route('/bugs/updatestatus/<id>',methods = ['PUT'])
def updatebugstatus(id):
    print("REST API call for updating status of a bug")
    bug = Bugs.query.get(id)
    if bug is None:
        return {"No bug with id ": id}
    bug.status = request.json['Status']

    db.session.add(bug)
    db.session.commit()
    return {f"status of bug {bug.id} ": f"updated to {bug.status}"}

@app.route('/bugs/addcomments/<id>',methods = ['POST'])
def addcomment(id):
    print("REST API call for updating a bug")
    bug = Bugs.query.get(id)
    if bug is None:
        return {"No bug with id ": id}
    comments = Comments()
    comments.comment = request.json['Comment']
    comments.bugid = id
    comments.commentedby = request.json['User']

    db.session.add(comments)
    db.session.commit()
    return {f"{comments.commentedby}":f"Commented on bug {comments.bugid}"}

@app.route('/bugs/<id>',methods = ['DELETE'])
def deletebug(id):
    bug = Bugs.query.get(id)
    if bug is None:
        return {"No bug with id ": id}
    comments=bug.comments
    for comment in comments:
        db.session.delete(comment)
    db.session.delete(bug)
    db.session.commit()
    return {"Deleted Bug": id}
    
serve(app,host='localhost',port=5000,threads=1)#WAITRESS

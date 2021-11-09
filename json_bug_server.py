from flask import Flask, request, jsonify
from waitress import serve
from flask_sqlalchemy import SQLAlchemy
import os

app =Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Bugs(db.Model):
    Bugid = db.Column(db.Integer, primary_key = True)
    Title = db.Column(db.String(100),nullable = False)
    Body = db.Column(db.String(500))
    Status = db.Column(db.String(10),nullable = False)
    CommentTitle = db.Column(db.String(100))
    CommentBody = db.Column(db.String(100))
#    AssignedTo = db.Column(db.Integer, db.ForeignKey('User.Userid'))

    def __repr__(self):
        return f"{self.Bugid}"
if not os.path.isfile('./data.db'):
    #create the Database
    print("creating the DB")
    db.create_all()
    db.session.commit()
else:
    print("DB already exsits")

@app.route('/')
def index():
    return("Welcome to BugsWorld !!")


@app.route('/bugs')
def GetBugs():
    print("REST API call for getting all bugs")
    bugs = Bugs.query.all()
    bugsJson = []
    for bug in bugs:
        bugsJson.append({"Bugid":bug.Bugid,"Title":bug.Title,"Body":bug.Body,"Status":bug.Status,"Comment":{"Title":bug.CommentTitle,"Body":bug.CommentBody}})
    #return {"bugs":bugsJson}
    return jsonify(bugsJson)

@app.route('/bugs/<id>')
def GetBug(id):
    print("REST API call for getting a specified bug")
    bug = Bugs.query.get(id)
    if bug is None:
        return {"No bug with id ": id}
    bugJson = ({"Bugid":bug.Bugid,"Title":bug.Title,"Body":bug.Body,"Status":bug.Status,"Comment":{"Title":bug.CommentTitle,"Body":bug.CommentBody}})
    return {"bug":bugJson}
    
@app.route('/bugs',methods = ['POST'])
def CreateBug():
    print("REST API call for creating a new bug")
    bug = Bugs()
    bug.Title = request.json['Title']
    bug.Body = request.json['Body']
    bug.Status = "unresolved"
    Comment = request.json['Comment']
    if Comment is not None:
        bug.CommentTitle = Comment['Title']
        bug.CommentBody = Comment['Body']
    db.session.add(bug)
    db.session.commit()
    return {"New Bug ID is":bug.Bugid}

@app.route('/bugs/<id>',methods = ['PUT'])
def UpdateBug(id):
    print("REST API call for updating a bug")
    bug = Bugs.query.get(id)
    if bug is None:
        return {"No bug with id ": id}
    bug.Title = request.json['Title']
    bug.Body = request.json['Body']
    bug.Status = request.json['Status']
    Comment = request.json['Comment']
    if Comment:
        bug.CommentTitle = Comment['Title']
        bug.CommentBody = Comment['Body']
    db.session.commit()
    return {"Updated bug : BugId":bug.Bugid}

@app.route('/bugs/<id>',methods = ['DELETE'])
def DeleteBug(id):
    bug = Bugs.query.get(id)
    if bug is None:
        return {"No bug with id ": id}
    db.session.delete(bug)
    db.session.commit()
    return {"Deleted Bug": id}
    
serve(app,host='localhost',port=5000,threads=1)#WAITRESS

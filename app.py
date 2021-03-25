from flask import Flask, request, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import logging, os, json
import uuid
import unittest
import requests

#config
class Config():
  SQLALCHEMY_DATABASE_URI = 'sqlite:///ongotester.sqlite3'
  SQLALCHEMY_TRACK_MODIFICATIONS = False

#init flask app
app = Flask (__name__)
app.config.from_object(Config)

# init database and serializer
db = SQLAlchemy(app)
ma = Marshmallow(app)

# db models
class User(db.Model):
   id = db.Column(db.Integer, primary_key = True)
   uuid = db.Column(db.String(100), nullable=False)
   name = db.Column(db.String(100), nullable=False)
   admin = db.Column(db.Boolean, default=False, nullable=False)
   tasks = db.relationship('Task', backref='author', lazy=True)
   follows = db.relationship('Follow', backref='author', lazy=True)

class Task(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  completed = db.Column(db.Boolean, default=False, nullable=False)
  content = db.Column(db.String(500), nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  follows = db.relationship('Follow', backref='task', lazy=True)

class Follow(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
  

#db serializers
class TaskSchema(ma.SQLAlchemySchema):
    class Meta:
      model = Task
      fields = ("id", "completed", "content")

task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

class FollowSchema(ma.SQLAlchemySchema):
    class Meta:
      model = Follow
      fields = ("id", "user_id", "task_id")

follow_schema = FollowSchema()
follows_schema = FollowSchema(many=True)

class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        fields = ("uuid", "name", "admin", "tasks", "follows")
    tasks = ma.Nested(TaskSchema, many=True)
    follows = ma.Nested(FollowSchema, many=True)

user_schema = UserSchema()
users_schema = UserSchema(many=True)

#views
@app.route('/', methods=['GET'])
def home():
  response = Response(
      response="healthy",
      status=200
  )
  return response
#users
@app.route('/api/new_user', methods=['POST'])
def new_user():
  data = json.loads(request.data)
  if 'admin' in data:
    try:
      name = data['name']
      new_uuid = uuid.uuid4()
      uuid_value = str(new_uuid)
      user = User(name=name, uuid=uuid_value, admin=True)
      db.session.add(user)
      db.session.commit()

      user_serialized = user_schema.dump(user)
      response = Response(
          response=json.dumps(user_serialized),
          status=201,
          mimetype='application/json'
      )

      return response
    except:
      raise

  else:
    try:
      name = data['name']
      new_uuid = uuid.uuid4()
      uuid_value = str(new_uuid)
      user = User(name=name, uuid=uuid_value)
      db.session.add(user)
      db.session.commit()

      user_serialized = user_schema.dump(user)
      response = Response(
          response=json.dumps(user_serialized),
          status=201,
          mimetype='application/json'
      )

      return response
    except:
      raise

#tasks
@app.route('/api/get_incomplete_tasks', methods=['GET'])
def get_incomplete_tasks():
  data = json.loads(request.data)
  try:
    user = db.session.query(User).filter_by(uuid=data['user_uuid']).first()
    tasks = Task.query.filter_by(completed=False, user_id=user.id).all()

    tasks_serialized = tasks_schema.dump(tasks)
    response = Response(
        response=json.dumps(tasks_serialized),
        status=200,
        mimetype='application/json'
    )

    return response
  except:
    raise

@app.route('/api/get_complete_tasks', methods=['GET'])
def get_complete_tasks():
  data = json.loads(request.data)
  try:
    user = db.session.query(User).filter_by(uuid=data['user_uuid']).first()
    tasks = Task.query.filter_by(completed=True, user_id=user.id).all()

    tasks_serialized = tasks_schema.dump(tasks)
    response = Response(
        response=json.dumps(tasks_serialized),
        status=200,
        mimetype='application/json'
    )

    return response
  except:
    raise


@app.route('/api/new_task', methods=['POST'])
def new_task():
  data = json.loads(request.data)
  if 'completed' in data:
    try:
      user = db.session.query(User).filter_by(uuid=data['user_uuid']).first()
      task = Task(content=data['content'], user_id=user.id, author=user, completed=True)
      db.session.add(task)
      db.session.commit()

      task_serialized = task_schema.dump(task)
      response = Response(
          response=json.dumps(task_serialized),
          status=201,
          mimetype='application/json'
      )

      return response
    except:
        raise
  else:
    try:
      user = db.session.query(User).filter_by(uuid=data['user_uuid']).first()
      task = Task(content=data['content'], user_id=user.uuid, author=user)
      db.session.add(task)
      db.session.commit()

      task_serialized = task_schema.dump(task)
      response = Response(
          response=json.dumps(task_serialized),
          status=201,
          mimetype='application/json'
      )

      return response
    except:
        raise

@app.route('/api/update_task', methods=['PUT'])
def update_task():
  data = json.loads(request.data)
  if 'completed' in data:
    try:
      task_to_update = db.session.query(Task).filter_by(id=data['task_id']).first()
      task_to_update.content = data['content']
      task_to_update.completed = True
      db.session.commit()

      task_serialized = task_schema.dump(task_to_update)
      response = Response(
          response=json.dumps(task_serialized),
          status=200,
          mimetype='application/json'
      )

      return response
    except:
        raise
  else:
    try:
      task_to_update = db.session.query(Task).filter_by(id=data['task_id']).first()
      task_to_update.content = data['content']
      db.session.commit()

      task_serialized = task_schema.dump(task_to_update)
      response = Response(
          response=json.dumps(task_serialized),
          status=200,
          mimetype='application/json'
      )

      return response
    except:
        raise

@app.route('/api/delete_task', methods=['DELETE'])
def delete_task():
  data = json.loads(request.data)
  try:
    task_to_delete = db.session.query(Task).filter_by(id=data['task_id']).first()
    db.session.delete(task_to_delete)
    db.session.commit()

    response = Response(
        response="task deleted!",
        status=200,
        mimetype='application/json'
    )

    return response
  except:
      raise

#follows
@app.route('/api/get_follows', methods=['GET'])
def get_following():
  data = json.loads(request.data)
  try:
    user = db.session.query(User).filter_by(uuid=data['user_uuid']).first()
    follows = Follow.query.filter_by(user_id=user.id).all()

    follows_serialized = follows_schema.dump(follows)
    response = Response(
        response=json.dumps(follows_serialized),
        status=200,
        mimetype='application/json'
    )

    return response
  except:
    raise


@app.route('/api/new_follow', methods=['POST'])
def new_follow():
  data = json.loads(request.data)
  try:
    user = db.session.query(User).filter_by(uuid=data['user_uuid']).first()
    task = db.session.query(Task).filter_by(id=data['task_id']).first()
    follow = Follow(user_id=user.uuid, author=user, task_id=task.id, task=task)
    db.session.add(follow)
    db.session.commit()

    follow_serialized = follow_schema.dump(follow)
    response = Response(
        response=json.dumps(follow_serialized),
        status=201,
        mimetype='application/json'
    )

    return response
  except:
    raise

@app.route('/api/delete_follow', methods=['DELETE'])
def delete_follow():
  data = json.loads(request.data)
  try:
    follow_to_delete = db.session.query(Follow).filter_by(id=data['follow_id']).first()
    db.session.delete(follow_to_delete)
    db.session.commit()

    response = Response(
        response="follow deleted!",
        status=200,
        mimetype='application/json'
    )

    return response
  except:
      raise

#admin
@app.route('/api/delete_user_data', methods=['DELETE'])
def delete_user_data():
  data = json.loads(request.data)
  try:
    user = db.session.query(User).filter_by(uuid=data['user_uuid']).first()

    if user.admin == True:
      try:
        target_user = db.session.query(User).filter_by(uuid=data['target_user_uuid']).first()
        db.session.query(Task).filter_by(user_id=target_user.id).delete()
        db.session.query(Follow).filter_by(user_id=target_user.id).delete()
        db.session.commit()

        response = Response(
            response="user data deleted!",
            status=200,
            mimetype='application/json'
        )

        return response
      except:
        raise
  except:
      raise

#tests
class IntegrationTests(unittest.TestCase):
  def setUp(self):
    self.baseUrl = 'http://127.0.0.1:5000/'

  def test_server_booted(self):
    res = requests.get(
      url=self.baseUrl,
    )
    self.assertEqual(res.status_code, 200)

  def _test_new_user(self, user_name: str):
    url = self.baseUrl + 'api/new_user'
    data = {
      "name": user_name
    }
    res = requests.post(
      url=url,
      data=json.dumps(data)
    )
    self.assertEqual(res.status_code, 201)

  def _test_new_admin_user(self, user_name: str):
    url = self.baseUrl + 'api/new_user'
    data = {
      "name": user_name,
      "admin": True
    }
    res = requests.post(
      url=url,
      data=json.dumps(data)
    )
    self.assertEqual(res.status_code, 201)
  
  def _test_new_task(self, user_uuid: str, content: str):
    url = self.baseUrl + 'api/new_task'
    data = {
      "user_uuid": user_uuid,
      "content": content
    }
    res = requests.post(
      url=url,
      data=json.dumps(data)
    )
    self.assertEqual(res.status_code, 201)

  def _test_new_complete_task(self, user_uuid: str, content: str):
    url = self.baseUrl + 'api/new_task'
    data = {
      "user_uuid": user_uuid,
      "content": content,
      "completed": True
    }
    res = requests.post(
      url=url,
      data=json.dumps(data)
    )
    self.assertEqual(res.status_code, 201)

  def _test_new_follow(self, user_uuid: str, task_id: int):
    url = self.baseUrl + 'api/new_follow'
    data = {
      "user_uuid": user_uuid,
      "task_id": task_id
    }
    res = requests.post(
      url=url,
      data=json.dumps(data)
    )
    self.assertEqual(res.status_code, 201)

  def _test_update_task(self, task_id: int, content: str):
    url = self.baseUrl + 'api/update_task'
    data = {
      "task_id": task_id,
      "content": content,
      "completed": True
    }
    res = requests.put(
      url=url,
      data=json.dumps(data)
    )
    self.assertEqual(res.status_code, 200)

  def _test_delete_task(self, task_id: int):
    url = self.baseUrl + 'api/delete_task'
    data = {
      "task_id": task_id
    }
    res = requests.delete(
      url=url,
      data=json.dumps(data)
    )
    self.assertEqual(res.status_code, 200)

  def _test_delete_follow(self, follow_id: int):
    url = self.baseUrl + 'api/delete_follow'
    data = {
      "follow_id": follow_id
    }
    res = requests.delete(
      url=url,
      data=json.dumps(data)
    )
    self.assertEqual(res.status_code, 200)

  def _test_get_incomplete_tasks(self, user_uuid: str):
    url = self.baseUrl + 'api/get_incomplete_tasks'
    data = {
      "user_uuid": user_uuid
    }
    res = requests.get(
      url=url,
      data=json.dumps(data)
    )
    self.assertEqual(res.status_code, 200)

  def _test_get_complete_tasks(self, user_uuid: str):
    url = self.baseUrl + 'api/get_complete_tasks'
    data = {
      "user_uuid": user_uuid
    }
    res = requests.get(
      url=url,
      data=json.dumps(data)
    )
    self.assertEqual(res.status_code, 200)

  def _test_delete_user_data(self, user_uuid: str, target_user_uuid: str):
    url = self.baseUrl + 'api/delete_user_data'
    data = {
      "user_uuid": user_uuid,
      "target_user_uuid": target_user_uuid
    }
    res = requests.delete(
      url=url,
      data=json.dumps(data)
    )
    self.assertEqual(res.status_code, 200)


  #test_app
  def test_app(self):
    #users
    self._test_new_user(user_name="not_admin")
    self._test_new_user(user_name="not_admin2")
    self._test_new_admin_user(user_name="admin")

    admin = db.session.query(User).filter_by(name="admin").first()
    not_admin = db.session.query(User).filter_by(name="not_admin").first()
    not_admin2 = db.session.query(User).filter_by(name="not_admin2").first()

    #new task
    self._test_new_task(user_uuid=not_admin.uuid, content="first uncomplete task by not_admin")
    self._test_new_task(user_uuid=not_admin2.uuid, content="first uncomplete task by not_admin2")
    self._test_new_task(user_uuid=not_admin.uuid, content="second uncomplete task by not_admin")
    self._test_new_task(user_uuid=not_admin2.uuid, content="second uncomplete task by not_admin2")
    self._test_new_task(user_uuid=not_admin.uuid, content="third uncomplete task by not_admin")
    self._test_new_task(user_uuid=not_admin2.uuid, content="third uncomplete task by not_admin2")
    # new complete task
    self._test_new_complete_task(user_uuid=not_admin.uuid, content="first complete task by not_admin")
    self._test_new_complete_task(user_uuid=not_admin2.uuid, content="first complete task by not_admin2")
    self._test_new_complete_task(user_uuid=not_admin.uuid, content="second complete task by not_admin")
    self._test_new_complete_task(user_uuid=not_admin2.uuid, content="second complete task by not_admin2")
    self._test_new_complete_task(user_uuid=not_admin.uuid, content="third complete task by not_admin")
    self._test_new_complete_task(user_uuid=not_admin2.uuid, content="third complete task by not_admin2")
    # new follow
    task_2 = db.session.query(Task).filter_by(content="first uncomplete task by not_admin2").first()
    task_4 = db.session.query(Task).filter_by(content="second uncomplete task by not_admin2").first()

    self._test_new_follow(user_uuid=not_admin.uuid, task_id=task_2.id)
    self._test_new_follow(user_uuid=not_admin.uuid, task_id=task_4.id)
    # update task
    self._test_update_task(task_id=task_2.id, content="first updated task by not_admin")
    self._test_update_task(task_id=task_4.id, content="first updated task by not_admin2")
    # delete task
    task_6 = db.session.query(Task).filter_by(content="third uncomplete task by not_admin2").first()

    self._test_delete_task(task_id=task_6.id)
    # delete follow 
    follow_1 = db.session.query(Follow).filter_by(task_id=task_4.id).first()

    self._test_delete_follow(follow_id=follow_1.id)
    # get incomplete tasks
    self._test_get_incomplete_tasks(user_uuid=not_admin.uuid)
    # get complete tasks
    self._test_get_complete_tasks(user_uuid=not_admin.uuid)
    # delete user data
    self._test_delete_user_data(user_uuid=admin.uuid, target_user_uuid=not_admin.uuid)

if __name__ == "__main__":
  app.run()


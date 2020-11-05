import markdown
import os
import shelve
import pymysql
import logging

from flask import Flask, g
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)

api = Api(app)

def get_db():
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = shelve.open('devices.db')
	return db

@app.teardown_appcontext
def teardown_db(exception):
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()

@app.route('/')
def index():
	'''Test documentation'''

	with open(os.path.dirname(app.root_path) + '/README.md', 'r') as md_file:

		content = md_file.read()

		return markdown.markdown(content)

class DeviceList(Resource):
	def get(self):
		con = pymysql.connect(host='172.17.0.1', port=6603, user='root', password='root', db='test')
		cur = con.cursor()

		q = f'''

		select *
		from devices

		'''

		count = cur.execute(q)

		columns = [el[0] for el in cur.description]
		row = cur.fetchall()

		data = [{columns[i]: row[j][i] for i in range(len(columns))} for j in range(count)]

		cur.close()
		con.close()

		return {'message': 'Success', 'data': data}

	def post(self):
		parser = reqparse.RequestParser()

		parser.add_argument('identifier', required=True)
		parser.add_argument('name', required=True)
		parser.add_argument('device_type', required=True)
		parser.add_argument('controller_gateway', required=True)

		args = parser.parse_args()

		con = pymysql.connect(host='172.17.0.1', port=6603, user='root', password='root', db='test')
		cur = con.cursor()

		q = f'''

		insert into devices
		values ({int(args['identifier'])}, '{args['name']}', '{args['device_type']}', '{args['controller_gateway']}')

		'''
		cur.execute(q)
		cur.fetchall()

		cur.close()
		con.commit()
		con.close()

		return {'message': 'Device registered', 'data': args}, 201

class Device(Resource):
	def get(self, identifier):

		con = pymysql.connect(host='172.17.0.1', port=6603, user='root', password='root', db='test')
		cur = con.cursor()

		q = f'''

		select *
		from devices
		where id = {identifier}

		'''

		count = cur.execute(q)

		columns = [el[0] for el in cur.description]
		row = cur.fetchall()

		data = {columns[i]: row[0][i] for i in range(len(columns))}

		cur.close()
		con.close()

		if count == 0:
			return {'message': 'Device not found', 'data': {}}, 404

		return {'message': 'Device found', 'data': data}, 200

	def delete(self, identifier):
		shelf = get_db()

		if not (identifier in shelf):
			return {'message': 'Device not found', 'data': {}}, 404

		del shelf[identifier]
		return '', 204

api.add_resource(DeviceList, '/devices')
api.add_resource(Device, '/device/<int:identifier>')

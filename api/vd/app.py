from flask import Flask, request, make_response, abort, Response
from flask_restful import Resource, Api
from errors import *
import datetime, time
import psycopg2, sys, json
import queries, middleware
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool


TEST_ASSIGNMENT = 0


DB_NAME = "vd"
USER = "vduser"
HOST = "db"
PASSWORD = "virtualdoctor"

MAX_CONNS = 20

i=0
while(i<10):
	try:
		conn = psycopg2.connect(database = DB_NAME, user = USER, password = PASSWORD, host = HOST)
		break
	except psycopg2.OperationalError as e:
		i+=1
		time.sleep(0.5)
		pass
conn = ThreadedConnectionPool(1, MAX_CONNS, dbname=DB_NAME, user=USER, password=PASSWORD, host=HOST).getconn()
cur = conn.cursor(cursor_factory=RealDictCursor)
DB = {'cur' : cur, 'conn' : conn}
#App setup

app = Flask(__name__)
api = Api(app)

class Case(Resource):
	""" insert a case """
	def post(self):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()"""
		user=1
		data = request.get_json(force=True)
		check_case_form(data)
		try:
			return output_json(queries.add_case(DB, data.get('timestamp'), data['stepsize'], data.get('description'), user), 201)
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except:
			DB['conn'].rollback()
			return internal_server_error()


def check_case_form(data):
	if data.get('stepsize_s') == None:
		abort(400)


class Cases(Resource):
	""" get all the cases of an user"""
	def get(self):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
		try:
			if (queries.check_admin(DB,user)):
				return output_json(queries.get_cases(DB),200)
            """
		try:
			user=1
			return output_json(queries.get_cases_user(DB, user),200)
		except psycopg2.Error as e:
			return internal_server_error_db(e)
		except:
			return internal_server_error()



class CaseState(Resource):
	""" get case info """
	def get(self, id):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
        if not (queries.check_owner(DB, id, user) or not (queries.check_admin(DB, id, user))):
        	return not_authorized()
		"""
		try:
			return output_json(queries.get_case_info(DB,id),200)
		except psycopg2.Error as e:
			return internal_server_error_db(e)
		except:
			return internal_server_error()

	""" modify case info """
	def put(self, id):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
        if not (queries.check_owner(DB, id, user)) or not (queries.check_admin(DB, id, user)):
        	return not_authorized()
		"""
		data = request.get_json(force=True)
		check_case_form(data)
		try:
			return queries.modify_case(DB, id, data.get('timestamp'), data['stepsize'], data.get('description'))
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except  Exception as e:
			DB['conn'].rollback()
			return internal_server_error()

	def delete(self, id):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
        if not (queries.check_admin(DB, id, user)):
        	return not_authorized()
		"""
		try:
			return queries.delete_case(DB, id)
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except:
			DB['conn'].rollback()
			return internal_server_error()



class States(Resource):
	"""get all the states info of the case"""
	def get(self, id):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
        if not (queries.check_owner(DB, id, user)) or not (queries.check_admin(DB, id, user)):
        	return not_authorized()
		"""
		try:
			return output_json(queries.get_states(DB,id),200)
		except psycopg2.Error as e:
			return internal_server_error_db(e)
		except:
			return internal_server_error()

class State(Resource):

	""" add a state in the case """
	def post(self, id):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
        if not (queries.check_owner(DB, id, user)) or not (queries.check_admin(DB, id, user)):
        	return not_authorized()
		"""
		data = request.get_json(force=True)
		check_state_form(data)
		try:
			return queries.add_state(DB, id, data['timestamp'])
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except:
			DB['conn'].rollback()
			return internal_server_error()


def check_state_form(data):
	if data.get('timestamp') == None:
		abort(400)

class StateInfo(Resource):
	""" modify a state"""
	def put(self, id, timestamp):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
        if not (queries.check_owner(DB, id, user)) or not (queries.check_admin(DB, id, user)):
        	return not_authorized()
		"""
		data = request.get_json(force=True)
		check_state_form(data)
		try:
			return queries.modify_state(DB, id, timestamp, data['timestamp'])
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except:
			DB['conn'].rollback()
			return internal_server_error()

	""" delete a state"""
	def delete(self, id, timestamp):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
        if not (queries.check_owner(DB, id, user)) or not (queries.check_admin(DB, id, user)):
        	return not_authorized()
		"""
		try:
			return queries.delete_state(DB,id,timestamp)
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except:
			DB['conn'].rollback()
			return internal_server_error()



class Assignments(Resource):
	""" get all the assignments of the state"""
	def get(self, id, timestamp):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
        if not (queries.check_owner(DB, id, user)) or not (queries.check_admin(DB, id, user)):
        	return not_authorized()
		"""
		try:
			return output_json(queries.get_assignments(DB, id, timestamp),200)
		except psycopg2.Error as e:
			return internal_server_error_db(e)
		except Exception as e:
			return internal_server_error()

class Assignment(Resource):
	""" add an assignment with the values"""
	def post(self, id, timestamp):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
        if not (queries.check_owner(DB, id, user)) or not (queries.check_admin(DB, id, user)):
        	return not_authorized()
		"""
		data = request.get_json(force=True)
		check_assignment_form(data)
		try:
			return queries.add_assignment(DB, id, timestamp, data['variable'], data['simplevariables'])
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except Exception as e:
			DB['conn'].rollback()
			internal_server_error()


def check_assignment_form(data):
	if data.get('variable') == None or data.get('simplevariables') == None:
		return abort(400)
	for value in data['simplevariables']:
		if value.get('simplevariable') == None or value.get('value') == None:
			return abort(400)


class AssignmentState(Resource):
	""" get assignment info """
	def get(self, id, timestamp, ordernum):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
        if not (queries.check_owner(DB, id, user)) or not (queries.check_admin(DB, id, user)):
        	return not_authorized()
		"""
		try:
			return output_json(queries.get_assignment(DB,id,timestamp,ordernum), 200)
		except psycopg2.Error as e:
			return internal_server_error_db(e)
		except:
			return internal_server_error()

	""" modify assignment info """
	def put(self, id, timestamp, ordernum):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
        if not (queries.check_owner(DB, id, user)) or not (queries.check_admin(DB, id, user)):
        	return not_authorized()
		"""
		data = request.get_json(force=True)
		check_assignment_form(data)
		try:
			return queries.modify_assignment(DB, id, timestamp, ordernum, data['variable'], data['simplevariables'])
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except Exception as e:
			DB['conn'].rollback()
			return internal_server_error()

	""" delete assignment """
	def delete(self, id, timestamp, ordernum):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()
        if not (queries.check_owner(DB, id, user)) or not (queries.check_admin(DB, id, user)):
        	return not_authorized()
		"""
		try:
			return queries.delete_assignment(DB,id,timestamp,ordernum)
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except:
			DB['conn'].rollback()
			return internal_server_error()



class Domains(Resource):
	""" get all the domains"""
	def get(self):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()"""
		try:
			return output_json(queries.get_domains(DB),200)
		except psycopg2.Error as e:
			return internal_server_error_db(e)
		except Exception as e:
			return str(e)
			return internal_server_error()


class Domain(Resource):
	""" add a domain"""
	def post(self):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()"""
		data = request.get_json(force=True)
		check_domain_form(data)
		try:
			return output_json(queries.add_domain(DB, data['type'], data['attributes']),201)
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except:
			DB['conn'].rollback()
			return internal_server_error()

def check_domain_form(data):
	if data.get('type') == None or data.get('attributes') == None:
		abort(400)
	for att in data['attributes']:
		if data['type'] != 'enumerate' and (data['attributes'].get('min') == None or data['attributes'].get('max') == None or data['attributes'].get('step') == None):
			abort(400)
		elif data['type'] == 'enumerate' and (data['attributes'].get('name') == None or data['attributes'].get('values') == None):
			abort(400)


class DomainState(Resource):
	""" get domain info"""
	def get(self,name):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()"""
		try:
			return output_json(queries.get_domain(DB, name), 200)
		except psycopg2.Error as e:
			return internal_server_error_db(e)
		except:
			return internal_server_error()

	""" modify a domain"""
	def put(self,name):
		"""user = middleware.get_user_from_request(request)
		if not user:
            return not_authenticated()
        if not (queries.check_admin(DB, id, user)):
        	return not_authorized()"""
		data = request.get_json(force=True)
		check_domain_form(data)
		try:
			return queries.modify_domain(DB, name, data['type'], data['attributes'])	
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except:
			DB['conn'].rollback()
			return internal_server_error()

	def delete(self,name):
		"""user = middleware.get_user_from_request(request)
		if not (queries.check_admin(DB, id, user)):
        	return not_authorized()"""
		try:
			return queries.delete_domain(DB, name)
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except:
			DB['conn'].rollback()
			return internal_server_error()



class Categories(Resource):
	""" get all the categories"""
	def get(self):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()"""
		try:
			return output_json(queries.get_categories(DB), 200)
		except psycopg2.Error as e:
			return internal_server_error_db(e)
		except:
			return internal_server_error()



def check_category_form(data):
	if data.get("supercategory") == None or data.get("category") == None:
		abort(400)



class Category(Resource):
	""" add a category"""
	def post(self):
		"""user = middleware.get_user_from_request(request)
        if not user:
            return not_authenticated()"""
		data = request.get_json(force=True)
		check_category_form(data)
		try:
			return queries.add_category(DB, data['supercategory'], data['category'])
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except:
			DB['conn'].rollback()
			return internal_server_error()


class CategoryState(Resource):
	"""delete a category """
	def delete(self, name):
		"""user = middleware.get_user_from_request(request)
		if not (queries.check_admin(DB, id, user)):
        	return not_authorized()"""
		try:
			return queries.delete_category(DB, name)
		except psycopg2.Error as e:
			DB['conn'].rollback()
			return internal_server_error_db(e)
		except:
			DB['conn'].rollback()
			return internal_server_error()


@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data, indent=8), code)
    resp.headers.extend(headers or {})
    return resp

# Routes

api.add_resource(Case, '/case')
api.add_resource(Cases, '/cases')
api.add_resource(CaseState, '/case/<int:id>')
api.add_resource(States, '/case/<int:id>/states')
api.add_resource(State, '/case/<int:id>/state')
api.add_resource(StateInfo, '/case/<int:id>/state/<int:timestamp>')
api.add_resource(Assignments,'/case/<int:id>/state/<int:timestamp>/assignments')
api.add_resource(Assignment,'/case/<int:id>/state/<int:timestamp>/assignment')
api.add_resource(AssignmentState,'/case/<int:id>/state/<int:timestamp>/assignment/<int:ordernum>')
api.add_resource(Domains, '/domains')
api.add_resource(Domain, '/domain')
api.add_resource(DomainState, '/domain/<string:name>')
api.add_resource(Categories, '/categories')
api.add_resource(Category, '/category')
api.add_resource(CategoryState, '/category/<string:name>')



if __name__ == '__main__':
	app.run(debug=True)
import psycopg2
from app import DB
from flask import abort
from errors import *

ADMIN_ROLE = 'admin'


def check_admin(DB, sub):
	cur = DB['cur']
	cur.execute("""SELECT * FROM users.userrole ur WHERE ur.sub = {} AND ur.role = {}""".format(sub, ADMIN_ROLE))
	return cur.fetchone()

def check_owner(DB, case, sub):
	cur = DB['cur']
	cur.execute("""SELECT * FROM public.retrospectivecase rc WHERE rc.id = {} AND rc.sub = {}""".format(case, sub))
	return cur.fetchone()



def add_case(DB, start, stepsize, description, user):
	cur = DB['cur']
	if start==None:
		start="NULL"
	else:
		start="'"+start+"'"
	if description==None:
		description="NULL"
	else:
		description="'"+description+"'"
	cur.execute("""
		INSERT INTO public.relcase
		VALUES (DEFAULT,{})
		RETURNING relcase.id
	""".format(stepsize))
	res = cur.fetchone()
	cur.execute("""
		INSERT INTO public.retrospectivecase
		VALUES ({},{},{},{})
	""".format(res['id'],description,start,user))
	DB['conn'].commit()
	return res



def get_cases(DB):
	cur = DB['cur']
	cur.execute("""SELECT c.id, rc.start::smallstring, c.stepsize_s, rc.description, rc.sub FROM public.relcase c, public.retrospectivecase rc WHERE c.id=rc.id""")
	res = cur.fetchall()
	if res == None:
		res = []
	return {'cases': [ { 'case' : x['id'], 'timestamp' : x['start'], 'stepsize' : x['stepsize_s'], 'description' : x['description'], 'user' : x['sub'] } for x in res]}



def get_cases_user(DB, user):
	cur = DB['cur']
	cur.execute("""SELECT c.id, rc.start::smallstring, c.stepsize_s, rc.description FROM public.relcase c, public.retrospectivecase rc WHERE rc.sub={} AND rc.id=c.id""".format(user))
	res = cur.fetchall()
	if res == None:
		res = []
	return {'cases': [ { 'case' : x['id'], 'timestamp' : x['start'], 'stepsize' : x['stepsize_s'], 'description' : x['description']} for x in res]}



def get_case_info(DB, id):
	cur = DB['cur']
	cur.execute("""SELECT c.id, rc.start::smallstring, c.stepsize_s, rc.description, rc.sub FROM public.relcase c, public.retrospectivecase rc WHERE c.id={} AND c.id=rc.id""".format(id))
	res = cur.fetchone()
	if res==None:
		return {}
	return {'case': { 'case' : res['id'], 'timestamp' : res['start'], 'stepsize' : res['stepsize_s'], 'description' : res['description'], 'user' : res['sub'] }}


def modify_case(DB, id, start, stepsize, description):
	cur = DB['cur']
	if start==None:
		start="NULL"
	else:
		start = "'"+start+"'"
	if description==None:
		description="NULL"
	else:
		description = "'"+description+"'"
	cur.execute("""UPDATE public.relcase c SET stepsize_s={} WHERE c.id={}""".format(stepsize,id))
	cur.execute("""UPDATE public.retrospectivecase rc SET start={}, description={} WHERE rc.id={}""".format(start,description,id))
	DB['conn'].commit()
	return 200



def delete_case(DB, id):
	cur = DB['cur']
	cur.execute("""DELETE FROM public.relcase c WHERE c.id={}""".format(id))
	DB['conn'].commit()
	return 200



def get_states(DB, id):
	cur = DB['cur']
	cur.execute("""SELECT * FROM public.state WHERE state.relcase={}""".format(id))
	res = cur.fetchall()
	if res == None:
		res = []
	return {'states': [ {'case' : x['relcase'], 'timestamp' : x['timestamp']}  for x in res]}



def add_state(DB, case, timestamp):
	cur = DB['cur']
	cur.execute("""INSERT INTO public.state VALUES({},{})""".format(case,timestamp))
	DB['conn'].commit()
	return 201



def modify_state(DB, case, old_timestamp, new_timestamp):
	cur = DB['cur']
	cur.execute("""UPDATE public.state  SET timestamp={} WHERE relcase={} AND timestamp={}""".format(new_timestamp,case,old_timestamp))
	DB['conn'].commit()
	return 200



def delete_state(DB, case, timestamp):
	cur = DB['cur']
	cur.execute("""DELETE FROM public.state WHERE relcase={} AND timestamp={}""".format(case,timestamp))
	DB['conn'].commit()
	return 200



def get_assignments(DB, case, timestamp):
	cur = DB['cur']
	cur.execute("""SELECT a.relcase, a.timestamp, a.ordernum, a.variable
		FROM public.assignment a
		WHERE a.relcase={} AND a.timestamp={}""".format(case,timestamp))
	assignments = cur.fetchall()
	if assignments==None:
		assignments=[]
	res = []
	for ass in assignments:
		temp={'order': ass['ordernum'], 'variable': ass['variable'], 'simplevariables': []}
		cur.execute("""
			SELECT svv.variable,svv.value::varchar(1000)
			FROM public.simplevariablevalue svv
			WHERE svv.relcase={} AND svv.timestamp={} AND svv.ordernum={}
			""".format(case,timestamp,ass['ordernum']))
		values = cur.fetchall()
		for v in values:
			temp['simplevariables'].append({'simplevariable' : v['variable'], 'value': v['value']})
		res.append(temp)
	return {'case': case, 'timestamp': timestamp, 'assignments': res }



def add_assignment(DB, case, timestamp, variable, simplevariables):
	cur = DB['cur']
	cur.execute("""
		SELECT max(ordernum) 
		FROM public.assignment a 
		WHERE a.relcase={} AND a.timestamp={}""".format(case,timestamp))
	res = cur.fetchone()
	ordernum=res['max']
	if ordernum==None:
		ordernum=1
	else:
		ordernum+=1
	cur.execute("""
		INSERT INTO public.assignment
		VALUES({},{},{},'{}')
		""".format(case, timestamp, ordernum, variable))
	for simple in simplevariables:
		cur.execute("""
		INSERT INTO public.simplevariablevalue
		VALUES({},{},{},'{}',{}::public.real)
		""".format(case, timestamp, ordernum, simple['simplevariable'], simple['value']))
	DB['conn'].commit()
	return 201



def get_assignment(DB, case, timestamp, ordernum):
	cur = DB['cur']
	cur.execute("""SELECT a.relcase, a.timestamp, a.ordernum, a.variable
		FROM public.assignment a
		WHERE a.relcase={} AND a.timestamp={} AND a.ordernum={}""".format(case,timestamp,ordernum))
	ass = cur.fetchone()
	if ass==None:
		return {}
	res=[]
	cur.execute("""
		SELECT svv.variable,svv.value::varchar(1000)
		FROM public.simplevariablevalue svv
		WHERE svv.relcase={} AND svv.timestamp={} AND svv.ordernum={}
		""".format(case,timestamp,ass['ordernum']))
	values = cur.fetchall()
	for v in values:
		res.append({'simplevariable' : v['variable'], 'value': v['value']})
	return {'case': case, 'timestamp': timestamp, 'order' : ass['ordernum'], 'variable' : ass['variable'], 'simplevariables': res }



def modify_assignment(DB, case, timestamp, ordernum, variable, variables_value):
	cur = DB['cur']
	cur.execute("""DELETE FROM public.assignment WHERE relcase={} AND timestamp={} AND ordernum={}""".format(case, timestamp, ordernum))
	cur.execute("""INSERT INTO public.assignment VALUES({}, {}, {},'{}') """.format(case, timestamp, ordernum, variable))
	for val in variables_value:
		cur.execute("""INSERT INTO public.SimpleVariableValue VALUES({}, {}, {}, '{}',{}::public.real) """.format(case, timestamp, ordernum, val['simplevariable'], val['value']))
	DB['conn'].commit()
	return 200



def delete_assignment(DB, case, timestamp, ordernum):
	cur = DB['cur']
	cur.execute("""DELETE FROM public.assignment WHERE relcase={} AND timestamp={} AND ordernum={}""".format(case, timestamp, ordernum))
	DB['conn'].commit()
	return 200



def add_domain(DB, type, attributes):
	cur = DB['cur']
	if type != 'enumerate':
		name = type + '_' + str(attributes['min']) + '_' + str(attributes['max']) + '_' + str(attributes['step'])
		cur.execute("""
			INSERT INTO public.domain
			VALUES('{}')
			""".format(name))
		cur.execute("""
			INSERT INTO public.rangedomain
			VALUES('{}', {}::public.real, {}::public.real, {}::public.realGZ, '{}')
			""".format(name, attributes['min'], attributes['max'], attributes['step'], type))
	elif type == 'enumerate':
		name = attributes['name']
		cur.execute("""
			INSERT INTO domain
			VALUES('{}')
			""".format(name))
		cur.execute("""
			INSERT INTO public.enumeratedomain
			VALUES('{}')
			""".format(name))
		i=1
		for value in attributes['values']:
			cur.execute("""
				INSERT INTO public.enumeratevalue
				VALUES('{}',{},'{}')
				""".format(name, i, value))
			i+=1
	DB['conn'].commit()
	return {'name': name}



def get_domains(DB):
	cur = DB['cur']
	cur.execute("""
		SELECT d.name FROM public.domain d;
		""")
	domains = cur.fetchall()
	res = []
	for dom in domains:
		cur.execute("""
			SELECT rd.min::varchar(1000), rd.max::varchar(1000), rd.step::varchar(1000), rd.type
			FROM public.rangedomain rd
			WHERE rd.domain='{}'
			""".format(dom['name']))
		temp = cur.fetchone()
		if temp == None:
			cur.execute("""
			SELECT ed.id, ed.value
			FROM public.enumeratevalue ed
			WHERE ed.domain='{}'
			""".format(dom['name']))
			temp = cur.fetchall()
			res.append({'domain' : dom['name'], 'type' : 'enumerate', 'attributes' : [{'id' : x['id'], 'value' : x['value'] }   for x in temp]})
		else:
			res.append({'domain' : dom['name'], 'type' : temp['type'], 'attributes' : {'min' : temp['min'], 'max' : temp['max'], 'step' : temp['step'] } })
	return {'domains': res}



def get_domain(DB, name):
	cur = DB['cur']
	res = {'name' : name}
	cur.execute("""SELECT * FROM public.rangedomain d WHERE d.domain='{}'""".format(name))
	test = cur.fetchone()
	if test==None:
		return {}
	cur.execute("""SELECT d.min::varchar(1000),d.max::varchar(1000),d.step::varchar(1000),d.type
		FROM public.rangedomain d
		WHERE d.domain='{}'
		""".format(name))
	dom = cur.fetchone()
	if dom == None:
		cur.execute("""SELECT ed.id,ed.value
		FROM public.enumeratevalue ed
		WHERE ed.domain='{}'
		""".format(name))
		values = cur.fetchall()
		res['type'] = 'enumerate'
		res['attributes'] = [ {'id' : x['id'], 'value' : x['value']} for x in values]
	else:
		res['type'] = dom['type']
		res['attributes'] = {'min' : dom['min'], 'max' : dom['max'], 'step' : dom['step']}
	return res



def modify_domain(DB, name, type, attributes):
	cur = DB['cur']
	if type == 'enumerate':
		cur.execute("""
			DELETE FROM public.enumeratedomain ed
			WHERE ed.domain='{}'
			""".format(name))
		cur.execute("""
			INSERT INTO public.enumeratedomain
			VALUES ('{}')
			""".format(name))
		cur.execute("""
			UPDATE public.domain
			SET name='{}'
			WHERE name='{}'
			""".format(attributes['name'], name))
		i = 1
		for val in attributes['values']:
			cur.execute("""
				INSERT INTO public.enumeratevalue
				VALUES('{}',{},'{}')
				""".format(attributes['name'],i,val))
			i+=1
	else:
		new_name = type + '_' + str(attributes['min']) + '_' + str(attributes['max']) + '_' + str(attributes['step']) 
		cur.execute(""" 
			UPDATE public.rangedomain
			SET domain='{}', min={}::public.real, max={}::public.real, step={}::public.realGZ, type='{}'
			WHERE domain='{}'
			""".format(new_name, attributes['min'], attributes['max'], attributes['step'], type, name))
		cur.execute("""
			UPDATE public.domain
			SET name='{}'
			WHERE name='{}'
			""".format(new_name, name))
	DB['conn'].commit()
	return 200


def delete_domain(DB, name):
	cur = DB['cur']
	cur.execute("""DELETE FROM public.domain
		WHERE name='{}'""".format(name))
	DB['conn'].commit()
	return 200


def get_categories(DB):
	cur = DB['cur']
	cur.execute("""SELECT * FROM public.category_tree('VDRootCategory')""")
	cat = cur.fetchall()
	res={'root':[]}
	for x in cat:
		if x['super'] == 'VDRootCategory':
			res['root'].append(x['sub']) 
			rec(cat, x['sub'], res)
	return res



def rec(cat, root, res): #Recursive function for category tree
	res[root] = []
	for x in cat:
		if x['super'] == root:
			res[root].append(x['sub'])
			new_cat = [x for x in cat if x['super'] != root]
			rec(new_cat,x['sub'],res)
	return res


def add_category(DB, supercategory, category):
	cur = DB['cur']
	if supercategory=="root":
		supercategory="VDRootCategory"
	cur.execute("""INSERT INTO public.category VALUES('{}') """.format(category))
	cur.execute("""INSERT INTO public.subcategory VALUES('{}','{}')""".format(supercategory, category))
	DB['conn'].commit()
	return 200


def delete_category(DB, category):
	cur = DB['cur']
	cur.execute("""DELETE FROM public.category WHERE name='{}' """.format(category))
	DB['conn'].commit()
	return 200

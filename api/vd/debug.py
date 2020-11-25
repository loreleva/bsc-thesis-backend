from flask import Flask, request, make_response, abort
from flask_restful import Resource, Api
from datetime import date
import psycopg2, sys
import queries, json

DB_NAME = "vd"
USER = "vduser"
HOST = "0.0.0.0"
PORT = "5432"
PASSWORD = "virtualdoctor"
try:
	conn = psycopg2.connect(database = DB_NAME, user = USER, host = HOST, port = PORT, password = PASSWORD)
except psycopg2.Error as e:
	print("Unable to connect ot the database:", e)
	sys.exit(-1)
cur = conn.cursor()
DB = {'cur' : cur, 'conn' : conn}

try:
	DB['cur'].execute("""INSERT INTO users.user values(1, 'aooo')""")
	#print(cur.fetchone())
	#print(DB['cur'].fetchone()[0])
	DB['conn'].commit()
	DB['cur'].close()
	DB['conn'].close()
except psycopg2.Error as e:
	print({'message' : 'Internal Server Error', 'code' : e.pgcode})



from flask import Response
import json

def internal_server_error_db(e):
	return Response(response=json.dumps({'message' : 'Internal Server Error', 'code' : e.pgerror, 'errorcode' : e.pgcode}), status=500)


def internal_server_error():
	return Response(response=json.dumps({'message' : 'Internal Server Error'}), status=500)


def not_authenticated():
    return Response(response=json.dumps({'message': 'Not Authenticated'}), status=401)


def not_authorized():
    return Response(response=json.dumps({'message': 'Not Authorized'}), status=403)
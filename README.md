# Bakcend
This is the Docker of the backend that i made during my internship.

# Database
The PostgreSQL database is implemented in the ```./db/sql/create.d``` folder.
- ```domains.sql``` contains the commands for the creation of the domains used in the database.
- ```functions.sql``` contains the trigger implemented in PLpgSQL
- ```relSchema.sql``` contains the commands for the creation of the tables

# APIs
The RESTful APIs are implemented in the ```./api/vd``` folder.
- ```app.py``` contains the implementation in Flask of the APIs. Here are defined the methods and the routes for the resources.
- ```queries.py``` contains the queries made to the PostgreSQL database, using the Python library psycopg2.
- ```middleware.py``` contains the functions to communicate with the authentication server.

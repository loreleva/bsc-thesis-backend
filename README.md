# Backend
This is the Docker of the backend that I made during my internship.
To run the program, launch the command ```docker-compose up```, from the project directory where is present the file ```docker-compose.yml```.

Once launched the docker, the APIs can be tested using the python file ```debug.py```. 
The file has to be runned from inside the docker of the APIs, at the path ```code/debug.py```.

# Database
The PostgreSQL database is implemented in the ```./db/sql/create.d``` folder.
- ```domains.sql``` contains the commands for the creation of the domains used in the database.
- ```functions.sql``` contains the trigger implemented in PLpgSQL.
- ```relSchema.sql``` contains the commands for the creation of the tables.

# APIs
The RESTful APIs have implemented in the ```./api/vd``` folder.
- ```app.py``` contains the implementation in Flask of the APIs. Here are implemented the functions associated with the HTTP methods and the URL routes for the resources.
- ```queries.py``` contains the queries made to the PostgreSQL database, using the Python library psycopg2.
- ```middleware.py``` contains the functions to communicate with the authentication server.

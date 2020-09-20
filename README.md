Set up a schemaless REST API database (as a docker container) for storing large amounts of data.
Also included is a simple Python3 library for connecting to RESTful databases.

Make sure python is installed on your system. 

Steps to set up RESTful API:

1) Install Docker and docker-compose as well as requirements under requirments.txt
    
    Install the following requirements
      flask
	    flask-restful
	    pymongo
      
    Install Docker and docker-compose                    
    - For Mac OS
    - Download Docker: https://docs.docker.com/docker-for-mac/install/
    - drag Docker to applications folder
    - Double click DMG docker file - Now Docker is on 
    - Check version : $ docker --version
                      $ docker-compose --version
                      $ docker-machine --version
                      
3) Clone this repository and spin up the doker container 
    $ git clone https://gitlab.com/librecube/elements/LC6501.git datastore
    $ cd datastore
    $ docker-compose up 
    
    Now, the database REST API is exposed to http://localhost:6501
    --> modify docker-compose.yml file to change port
    
    3.1) If you don't have docker
          $ git clone https://gitlab.com/librecube/elements/LC6501.git datastore
          $ cd datastore
          $ python -m venv venv
          $ source venv/bin/activate
          $ pip install -r requirements.txt
          
          Now you start a python script ($ python3), then input the following code
    
          >>> from application import Application
          >>> app = Application()
          >>> app.run(port=6501)
          
          From your terminal you should see...
          
           * Serving Flask app "application" (lazy loading)
           * Environment: production
          WARNING: This is a development server. Do not use it in a production deployment.
          Use a production WSGI server instead.
          * Debug mode: off
          * Running on http://127.0.0.1:6501/ (Press CTRL+C to quit)

4) Now, gain access to a simple Python3 library for connecting to RESTful databases

  From terminal:
  $ pip install git+https://gitlab.com/librecube/lib/python-rest-db-client
  
  
  4.1) Now you can open a python script or shell while your docker-compose is up to and create a client..
      
        from rest_db_client import RestDbClient
        client = RestDbClient(port=6501)
        
The RESTful database is expected to organize its data in terms of , data is
organized as domains and models. To access the data of domains and models,
like so:

    domain = client['Galaxy']
    model = domain['SolarSystem']

      
      


    


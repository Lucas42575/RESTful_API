from application import Application
from rest_db_client import RestDbClient
import requests
client = RestDbClient(port=6501)
#app = Application()
#app.run(port = 6501)
import sys
import json
import pandas as pd
import requests
app = Application()


if __name__ == "__main__":
    response = requests.get('http://127.0.0.1:6501/')
    print(response.status_code)
    try:
        # checks if source file was passed and if it exists
        if len(sys.argv) != 2:
            raise ValueError("Error - Missing source file")
        flight_data_frame = pd.read_excel(sys.argv[1])
        print(sys.argv[1], "Loaded successfully into pandas dataframe")
    except Exception as e:
        print(e)

    domain = client['ModelTest']
    model = domain['domainTest']


    documents = [
    {
        'planet': 'Jupiter',
        'moons': 69
    },
    {
        'planet': 'Mars'
    },
    {
        'planet': 'Earth',
        'moons': 1,
        'inhabited': True
    },
    ]
    model.insert(documents)

    documents = model.find(
    filter={'moons': {'ge': 1}},
    fields=['planet'],
    sort=['-moons']
    )






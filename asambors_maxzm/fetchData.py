import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
from requests import request as rq

class fetchData(dml.Algorithm):
    contributor = 'asambors_maxzm'
    reads = []
    writes = ['asambors_maxzm.hospitals', 'asambors_maxzm.nosleep', 'asambors_maxzm.energywater', 'asambors_maxzm.ziptoincome', 'asambors_maxzm.zipcodetolatlong']

    @staticmethod
    def execute(trial = False):
        '''Retrieve necessary data set.'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('asambors_maxzm', 'asambors_maxzm')

        data_urls = {
            "hospitals": 'https://data.cityofboston.gov/resource/u6fv-m8v4.json',
            "energywater":'https://data.cityofboston.gov/resource/vxhe-ma3y.json',
            "ziptoincome": 'http://datamechanics.io/data/asambors_maxzm/zipCodeSallaries.json',
            "zipcodetolatlong": 'http://datamechanics.io/data/asambors_maxzm/zipcodestolatlong.json'
        }

        for key in data_urls:  
            url = data_urls[key]
            response = urllib.request.urlopen(url).read().decode("utf-8")
            r = json.loads(response)
            # s = json.dumps(r, sort_keys=True, indent=2)
            # print(s)

            repo.dropCollection(key)
            repo.createCollection(key)
            repo['asambors_maxzm.'+key].insert_many(r)
            repo['asambors_maxzm.'+key].metadata({'complete':True})


        sleep_soda_api = 'https://chronicdata.cdc.gov/resource/eqbn-8mpz.json'
        response = rq(method="GET", url=url) 
        r = response.json()

        repo.dropCollection('nosleep')
        repo.createCollection('nosleep')
        repo['asambors_maxzm.nosleep'].insert_many(r)
        repo['asambors_maxzm.nosleep'].metadata({'complete':True})

        repo.logout()
        endTime = datetime.datetime.now()
        return {"start":startTime, "end":endTime}
        
    
    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
        '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('asambors_maxzm', 'asambors_maxzm')

        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        
        # ADD THREE DATA SOURCES
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/') # Boston Data Portal
        doc.add_namespace('datm', 'http://datamechanics.io/data/') # datamechanics.io
        doc.add_namespace('cdc', 'https://chronicdata.cdc.gov/resource/') # CDC Data Portal

        this_script = doc.agent('alg:asambors_maxzm#example', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})

        # BOSTON DATA PORTAL
        hospitals_resource = doc.entity('bdp:u6fv-m8v4', {'prov:label':'Hospital Locations', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        energy_resource = doc.entity('bdp:vxhe-ma3y', {'prov:label':'Building Energy and Water Use Metrics', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})

        # CDC DATA
        sleep_resource = doc.entity('cdc:eqbn-8mpz', {'prov:label':'Sleeping less than 7 hours among adults aged >=18 years', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        
        # DATAMECHANICS.IO DATA
        zip_to_income_resource = doc.entity('datm:asambors_maxzm', {'prov:label':'Zip code to estimated income', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        lat_to_zip_resource = doc.entity('datm:asambors_maxzm', {'prov:label':'Latitude, longitude to zip code', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})

        get_hospitals = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime, {'prov:label':'Hospital Locations'})
        get_energy = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime, {'prov:label':'Building Energy and Water Use Metrics'})
        get_sleep = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime, {'prov:label':'Sleeping less than 7 hours among adults aged >=18 years'})
        get_zip_to_income = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime, {'prov:label':'Zip code to estimated income'})
        get_lat_to_zip = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime, {'prov:label':'Latitude, longitude to zip code'})

        doc.wasAssociatedWith(get_hospitals, this_script)
        doc.wasAssociatedWith(get_energy, this_script)
        doc.wasAssociatedWith(get_sleep, this_script)
        doc.wasAssociatedWith(get_zip_to_income, this_script)
        doc.wasAssociatedWith(get_lat_to_zip, this_script)

        doc.usage(get_hospitals, hospitals_resource, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':'?$select=location&$limit=11000000'
                }
            )

        doc.usage(get_energy, energy_resource, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':'?$select=location&$limit=11000000'
                }
            )

        doc.usage(get_sleep, sleep_resource, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':'?$select=location&$limit=11000000'
                }
            )

        doc.usage(get_zip_to_income, zip_to_income_resource, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':'?$select=location&$limit=11000000'
                }
            )

        doc.usage(get_lat_to_zip, lat_to_zip_resource, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':'?$select=location&$limit=11000000'
                }
            )

        Hospitals = doc.entity('dat:asambors_maxzm#hospitals', {prov.model.PROV_LABEL:'Animals Lost', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(lost, this_script)
        doc.wasGeneratedBy(lost, get_lost, endTime)
        doc.wasDerivedFrom(lost, resource, get_lost, get_lost, get_lost)

        Energy = doc.entity('dat:asambors_maxzm#energywater', {prov.model.PROV_LABEL:'Animals Lost', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(lost, this_script)
        doc.wasGeneratedBy(lost, get_lost, endTime)
        doc.wasDerivedFrom(lost, resource, get_lost, get_lost, get_lost)

        Sleep = doc.entity('dat:asambors_maxzm#nosleep', {prov.model.PROV_LABEL:'Animals Lost', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(lost, this_script)
        doc.wasGeneratedBy(lost, get_lost, endTime)
        doc.wasDerivedFrom(lost, resource, get_lost, get_lost, get_lost)

        ZipToIncome = doc.entity('dat:asambors_maxzm#ziptoincome', {prov.model.PROV_LABEL:'Animals Lost', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(lost, this_script)
        doc.wasGeneratedBy(lost, get_lost, endTime)
        doc.wasDerivedFrom(lost, resource, get_lost, get_lost, get_lost)

        LatLongToIncome = doc.entity('dat:asambors_maxzm#zipcodetolatlong', {prov.model.PROV_LABEL:'Animals Lost', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(lost, this_script)
        doc.wasGeneratedBy(lost, get_lost, endTime)
        doc.wasDerivedFrom(lost, resource, get_lost, get_lost, get_lost)

        repo.logout()
                  
        return doc

fetchData.execute()
# doc = fetchData.provenance()
# print(doc.get_provn())
# print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof
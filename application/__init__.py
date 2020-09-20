import os
import bson
import json
import zipfile

import pymongo
from flask import Flask, request, abort, send_file
from flask_restful import Api, Resource

from .http import success, register_error_handlers
from .utils import to_objectid_or_int, to_json, import_from_dump, zip_dump


DEFAULT_PAGESIZE = 100
client = pymongo.MongoClient(host=os.environ.get('MONGO_HOST', 'localhost'))


class Application(Flask):

    def __init__(self):
        super().__init__(__package__)
        register_error_handlers(self)

        self.api = Api(self)
        self.api.add_resource(Domains, '/')
        self.api.add_resource(Exporter, '/_export')
        self.api.add_resource(Importer, '/_import')
        self.api.add_resource(
            DomainModels, '/<domain>', '/<domain>/')
        self.api.add_resource(
            DomainModelDocuments, '/<domain>/<model>', '/<domain>/<model>/')
        self.api.add_resource(
            DomainModelDocumentInstance,
            '/<domain>/<model>/<_id>', '/<domain>/<model>/<_id>/')


class Exporter(Resource):

    def get(self):
        """A a zip file containing the dump of the entire database content.
        """
        dump = {}
        domains = client.list_database_names()
        domains = set(domains) - set(['admin', 'config', 'local'])
        for domain in domains:
            models = client[domain].list_collection_names()
            dump[domain] = {}
            for model in models:
                documents = client[domain][model].find()
                dump[domain][model] = []
                for document in documents:
                    del document['_id']
                    dump[domain][model].append(document)
        file = zip_dump(dump)
        return send_file(
            file, attachment_filename='dump.zip', as_attachment=True)


class Importer(Resource):

    def post(self):
        f = request.files['dump']
        number_of_entries = 0
        with zipfile.ZipFile(f) as zf:
            with zf.open('dump.json') as content:
                dump = json.loads(content.read())
                number_of_entries = import_from_dump(client, dump)
        return success(200, 'imported', count=number_of_entries)


class Domains(Resource):

    def get(self):
        """Returns a list of all domains in the database.
        """
        domains = sorted(client.list_database_names())
        return domains


class DomainModels(Resource):

    def get(self, domain):
        """Returns a list of all models of the given domain.
        """
        db = client[domain]
        if domain not in client.list_database_names():
            abort(404)
        models = sorted(db.list_collection_names())
        return models

    def delete(self, domain):
        """Delete an entire domain.
        """
        if domain not in client.list_database_names():
            abort(404)
        client.drop_database(domain)
        return success(200, 'deleted', count=1)


class DomainModelDocuments(Resource):

    def get(self, domain, model):
        """Returns all the entries of the given domain model,
        subject to filtering and other parameters.
        """
        db = client[domain]
        collection = db[model]
        if model not in db.list_collection_names():
            abort(404)
        # filtering
        query = filter_collection(request)
        # projection
        if '_fields' in request.args.keys():
            projection = {}
            values = request.args['_fields'].split(',')
            for value in values:
                projection[value] = 1
        else:
            projection = None
        # execute query
        documents = collection.find(query, projection)
        # sorting
        sort = []
        for value in request.args.getlist('_sort'):
            values = value.split(',')
            for value in values:
                if value.startswith('-'):
                    sort.append((value[1:], pymongo.DESCENDING))
                elif value.startswith('+'):
                    sort.append((value[1:], pymongo.ASCENDING))
                else:
                    sort.append((value, pymongo.ASCENDING))
        if sort:
            documents.sort(sort)
        # limiting and paging
        if '_limit' in request.args.keys():
            limit = int(request.args.get('_limit'))
            documents.limit(limit)
        elif '_page' in request.args.keys():
            page = int(request.args.get('_page'))
            if '_pagesize' in request.args.keys():
                pagesize = int(request.args.get('_pagesize'))
            else:
                pagesize = DEFAULT_PAGESIZE
            documents.skip((page - 1) * pagesize).limit(pagesize)
        return to_json(documents)

    def post(self, domain, model):
        collection = get_collection(domain, model)
        documents = request.get_json(silent=True)
        if not documents:
            abort(400, 'The request did not include JSON data.')
        if not isinstance(documents, list):
            documents = [documents]
        # ensure that _id is not given in the body
        for document in documents:
            if '_id' in document.keys():
                abort(422, 'Supplying an _id field is not allowed.')
        result = collection.insert_many(documents)
        if len(documents) == 1:
            inserted_id = str(result.inserted_ids[0])
            return success(201, 'created', count=1,
                           location='/'.join([domain, model, inserted_id]))
        else:
            return success(201, 'created', count=len(documents))

    def delete(self, domain, model):
        """Delete the full domain model or a subset of its documents.
        """
        db = client[domain]
        collection = db[model]
        if model not in db.list_collection_names():
            abort(404)
        if not request.args:
            db.drop_collection(model)
            return success(200, 'deleted', count=1)
        # filtering
        query = filter_collection(request)
        # execute query
        result = collection.delete_many(query)
        return success(200, 'deleted', count=result.deleted_count)


class DomainModelDocumentInstance(Resource):

    def get(self, domain, model, _id):
        """Returns the instance with the given id of the domain model.
        """
        collection = get_collection(domain, model)
        # filtering
        query = {'_id': to_objectid_or_int(_id)}
        # projection
        if '_fields' in request.args.keys():
            projection = {}
            values = request.args['_fields'].split(',')
            for value in values:
                projection[value] = 1
        else:
            projection = None
        # execute query
        document = collection.find_one(query, projection)
        if not document:
            abort(404)
        return to_json(document)

    def put(self, domain, model, _id):
        """Replace the instance with the given id of the domain model.
        """
        collection = get_collection(domain, model)
        document = request.get_json(silent=True)
        if not document:
            abort(400, 'The request did not include JSON data.')
        if isinstance(document, list):
            abort(400, 'Data must not be provided as a list.')
        # ensure that _id is not given in the body
        if '_id' in document.keys():
            abort(422, 'Supplying an _id field is not allowed.')
        query = {'_id': to_objectid_or_int(_id)}
        result = collection.replace_one(query, document, upsert=False)
        if result.matched_count == 0:
            return abort(404)
        else:
            return success(200, 'replaced', count=1)

    def patch(self, domain, model, _id):
        """Modify the instance with the given id of the domain model.
        """
        collection = get_collection(domain, model)
        document = request.get_json(silent=True)
        if not document:
            abort(400, 'The request did not include JSON data.')
        if isinstance(document, list):
            abort(400, 'Data must not be provided as a list.')
        # ensure that _id is not given in the body
        if '_id' in document.keys():
            abort(422, 'Supplying an _id field is not allowed.')
        query = {'_id': to_objectid_or_int(_id)}
        result = collection.update_one(query, {'$set': document})
        if result.matched_count == 0:
            abort(404)
        else:
            return success(200, 'modified', count=1)

    def delete(self, domain, model, _id):
        """Deletes the instance with the given id of the domain model.
        """
        collection = get_collection(domain, model)
        # filtering
        query = {'_id': to_objectid_or_int(_id)}
        # execute query
        result = collection.delete_one(query)
        if result.deleted_count == 0:
            abort(404)
        return success(200, 'deleted', count=1)


def get_collection(domain, model):
    db = client[domain]
    collection = db[model]
    return collection


def filter_collection(request):
    """
    Returns a query object that can be passed to pymongo for filtering. The
    query is assembled from the parameters that are passed in the request.
    """
    query = {}
    for key in request.args.keys():
        if key == '_id' or not key.startswith('_'):
            for values in request.args.getlist(key):
                operator = None
                if ':' not in values:
                    operator = '$in'
                elif values.startswith('in:'):
                    operator = '$in'
                    values = values[3:]
                elif values.startswith('lt:'):
                    operator = '$lt'
                    values = values[3:]
                elif values.startswith('le:'):
                    operator = '$lte'
                    values = values[3:]
                elif values.startswith('gt:'):
                    operator = '$gt'
                    values = values[3:]
                elif values.startswith('ge:'):
                    operator = '$gte'
                    values = values[3:]
                elif values.startswith('nin:'):
                    operator = '$nin'
                    values = values[4:]
                if operator:
                    if key == '_id':
                        try:
                            values = [
                                bson.ObjectId(value) for value
                                in values.split(',')]
                        except bson.errors.InvalidId:
                            values = [
                                float(value) for value in values.split(',')]
                    else:
                        try:
                            # try to convert filter value to number unless
                            # is is marked as a string value
                            values = [
                                float(value) if not value.startswith('"') else
                                value[1::-2] for value in values.split(',')]
                        except ValueError:
                            values = [
                                str(value) for value in values.split(',')]
                    
                    if operator != '$in' and operator != '$nin':
                        values = values[0]
                    if key in query:
                        query[key][operator] = values
                    else:
                        query[key] = {operator: values}
    return query

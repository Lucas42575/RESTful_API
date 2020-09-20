import io
import bson
import json
import zipfile
from flask import jsonify, abort


def to_json(documents):
    """
    Returns a valid JSON object from a list of dictionaries
    """
    if isinstance(documents, dict):
        output = {}
        for key, value in documents.items():
            if isinstance(value, bson.ObjectId):
                value = str(value)
            output[key] = value
    else:
        output = []
        for document in documents:
            field = {}
            for key, value in document.items():
                if isinstance(value, bson.ObjectId):
                    value = str(value)
                field[key] = value
            output.append(field)
    return jsonify(output)


def to_objectid_or_int(_id):
    try:
        _id = bson.ObjectId(_id)
    except bson.errors.InvalidId:
        try:
            _id = int(_id)
        except ValueError:
            abort(400, 'The _id is not of a valid format. '
                       'Allowed are ObjectId or int.')
    return _id


def zip_dump(dump):
    mem_file = io.BytesIO()
    with zipfile.ZipFile(mem_file, 'w') as zf:
        handle = zipfile.ZipInfo('dump.json')
        zf.writestr(
            handle, json.dumps(dump, indent=2),
            compress_type=zipfile.ZIP_DEFLATED)
    mem_file.seek(0)
    return mem_file


def import_from_dump(client, dump):
    number_of_entries = 0

    for domain in dump.keys():
        for model in dump[domain].keys():
            number_of_entries += len(dump[domain][model])
            client[domain][model].insert_many(dump[domain][model])
    return number_of_entries

import unittest
import json

import pymongo

from application import Application
app = Application()

# endpoints for testing
DUMMY_DOMAIN = 'dummy_domain'
DUMMY_MODEL = 'dummy_model'
DUMMY_ENDPOINT = DUMMY_DOMAIN + '/' + DUMMY_MODEL
NONEXISTING_DOMAIN = 'non_existent_domain'
NONEXISTING_MODEL = 'non_existent_model'


def post_json(client, url, json_dict):
    return client.post(
        url, data=json.dumps(json_dict), content_type='application/json')


def put_json(client, url, json_dict):
    return client.put(
        url, data=json.dumps(json_dict), content_type='application/json')


def patch_json(client, url, json_dict):
    return client.patch(
        url, data=json.dumps(json_dict), content_type='application/json')


def json_of_response(response):
    return json.loads(response.data.decode('utf8'))


def delete_database(db_client, database):
    db_client.drop_database(database)


def set_up(self):
    self.app = app
    self.app_context = self.app.app_context()
    self.app_context.push()
    self.client = self.app.test_client()
    self.db_client = pymongo.MongoClient(host='mongo')


class CreateTestCase(unittest.TestCase):
    def setUp(self):
        set_up(self)
        delete_database(self.db_client, DUMMY_DOMAIN)

    def tearDown(self):
        self.app_context.pop()
        delete_database(self.db_client, DUMMY_DOMAIN)

    def test_post_to_domain(self):
        response = self.client.post(DUMMY_DOMAIN)
        assert response.status_code == 405

    def test_post_to_model_without_json(self):
        response = self.client.post(DUMMY_ENDPOINT)
        assert response.status_code == 400

    def test_post_to_model_with_empty_json(self):
        response = post_json(self.client, DUMMY_ENDPOINT, {})
        assert response.status_code == 400

    def test_create_single_entry(self):
        # both json element and json list should be allowed
        response = post_json(self.client, DUMMY_ENDPOINT,
                             {'dummy': True})
        assert response.status_code == 201

        response = post_json(self.client, DUMMY_ENDPOINT,
                             [{'dummy': True}])
        assert response.status_code == 201

    def test_create_two_entries(self):
        domain = self.db_client[DUMMY_DOMAIN]
        model = domain[DUMMY_MODEL]
        no_of_docs = model.count_documents(filter={})
        response = post_json(
            self.client, DUMMY_ENDPOINT,
            [
                {'dummy': True},
                {'dummy': True}
            ])
        assert response.status_code == 201
        assert no_of_docs + 2 == model.count_documents(filter={})

    def test_create_document_with_id(self):
        response = post_json(self.client, DUMMY_ENDPOINT,
                             [{'_id': 100, 'dummy': True}])
        assert response.status_code == 422

    def test_create_with_id_in_url(self):
        response = post_json(self.client, DUMMY_ENDPOINT + '/100',
                             {'dummy': True})
        assert response.status_code == 405

    def test_create_with_id_in_body(self):
        response = post_json(self.client, DUMMY_ENDPOINT,
                             [{'_id': 100, 'dummy': True}])
        assert response.status_code == 422


class ReadTestCase(unittest.TestCase):
    def setUp(self):
        set_up(self)
        delete_database(self.db_client, DUMMY_DOMAIN)
        response = post_json(self.client, DUMMY_ENDPOINT,
                             [{'dummy': True}])
        self.dummy_entry_id = response.location.split('/')[-1]
        assert response.status_code == 201

    def tearDown(self):
        self.app_context.pop()
        delete_database(self.db_client, DUMMY_DOMAIN)

    def test_root_url(self):
        response = self.client.get('/')
        assert response.status_code == 200

    def test_read_nonexisting_domain(self):
        response = self.client.get(NONEXISTING_DOMAIN)
        assert response.status_code == 404

    def test_read_nonexisting_model(self):
        response = self.client.get(DUMMY_DOMAIN + '/' + NONEXISTING_MODEL)
        assert response.status_code == 404

    def test_read_nonexisting_id(self):
        response = self.client.get(DUMMY_ENDPOINT + '/100')
        assert response.status_code == 404

    def test_read_existing_domain(self):
        response = self.client.get(DUMMY_DOMAIN)
        assert response.status_code == 200

    def test_read_existing_model(self):
        response = self.client.get(DUMMY_DOMAIN + '/' + DUMMY_MODEL)
        assert response.status_code == 200

    def test_read_existing_id(self):
        response = self.client.get(DUMMY_ENDPOINT + '/' + self.dummy_entry_id)
        assert response.status_code == 200


class DeleteTestCase(unittest.TestCase):
    def setUp(self):
        set_up(self)
        delete_database(self.db_client, DUMMY_DOMAIN)
        response = post_json(self.client, DUMMY_ENDPOINT,
                             [{'dummy': True}])
        self.dummy_entry_id = response.location.split('/')[-1]
        assert response.status_code == 201

    def tearDown(self):
        self.app_context.pop()
        delete_database(self.db_client, DUMMY_DOMAIN)

    def test_delete_existing_domain(self):
        response = self.client.get(DUMMY_DOMAIN)
        assert response.status_code == 200

        response = self.client.delete(DUMMY_DOMAIN)
        assert response.status_code == 200

        response = self.client.get(DUMMY_DOMAIN)
        assert response.status_code == 404

    def test_delete_existing_model(self):
        response = self.client.get(DUMMY_ENDPOINT)
        assert response.status_code == 200

        response = self.client.delete(DUMMY_ENDPOINT)
        assert response.status_code == 200

        response = self.client.get(DUMMY_ENDPOINT)
        assert response.status_code == 404

    def test_delete_existing_id(self):
        response = self.client.get(DUMMY_ENDPOINT + '/' + self.dummy_entry_id)
        assert response.status_code == 200

        response = self.client.delete(
            DUMMY_ENDPOINT + '/' + self.dummy_entry_id)
        assert response.status_code == 200

        response = self.client.get(DUMMY_ENDPOINT + '/' + self.dummy_entry_id)
        assert response.status_code == 404

    def test_delete_nonexisting_domain(self):
        response = self.client.get(NONEXISTING_DOMAIN)
        assert response.status_code == 404

        response = self.client.delete(NONEXISTING_DOMAIN)
        assert response.status_code == 404

    def test_delete_nonexisting_model(self):
        response = self.client.get(DUMMY_DOMAIN + NONEXISTING_MODEL)
        assert response.status_code == 404

        response = self.client.delete(DUMMY_DOMAIN + NONEXISTING_MODEL)
        assert response.status_code == 404

    def test_delete_nonexisting_id(self):
        response = self.client.get(
            DUMMY_ENDPOINT + '/5b07f6ef48e7553a10c05ab7')
        assert response.status_code == 404

        response = self.client.delete(
            DUMMY_ENDPOINT + '/5b07f6ef48e7553a10c05ab7')
        assert response.status_code == 404


class UpdateTestCase(unittest.TestCase):
    def setUp(self):
        set_up(self)
        delete_database(self.db_client, DUMMY_DOMAIN)
        response = post_json(self.client, DUMMY_ENDPOINT,
                             [{'dummy': True, 'second': True}])
        self.dummy_entry_id = response.location.split('/')[-1]
        assert response.status_code == 201

    def tearDown(self):
        self.app_context.pop()
        delete_database(self.db_client, DUMMY_DOMAIN)

    def test_put_on_domain(self):
        response = put_json(self.client, DUMMY_DOMAIN, [{'dummy': True}])
        assert response.status_code == 405

    def test_put_on_nonexisting_domain(self):
        response = put_json(self.client, NONEXISTING_DOMAIN, [{'dummy': True}])
        assert response.status_code == 405

    def test_put_on_model(self):
        response = put_json(self.client, DUMMY_ENDPOINT, [{'dummy': True}])
        assert response.status_code == 405

    def test_put_on_nonexisting_model(self):
        response = put_json(
            self.client, DUMMY_DOMAIN + NONEXISTING_MODEL, [{'dummy': True}])
        assert response.status_code == 405

    def test_put_without_json(self):
        # suppress TypeError
        with self.assertRaises(TypeError):
            put_json(self.client, DUMMY_ENDPOINT)

    def test_put_with_empty_json(self):
        response = put_json(
            self.client, DUMMY_ENDPOINT + '/' + self.dummy_entry_id, {})
        assert response.status_code == 400

    def test_put_updates_entry(self):
        response = put_json(
            self.client, DUMMY_ENDPOINT + '/' + self.dummy_entry_id,
            {'dummy': False})
        assert response.status_code == 200
        response = json_of_response(
            self.client.get(DUMMY_ENDPOINT + '/' + self.dummy_entry_id))
        assert response == {'_id': self.dummy_entry_id, 'dummy': False}

    def test_put_creates_new_entry_should_fail(self):
        response = put_json(
            self.client, DUMMY_ENDPOINT + "/5b07f6ef48e7553a10c05ab7",
            {'dummy': True})
        assert response.status_code == 404

    def test_put_expects_single_json_gets_list(self):
        response = put_json(
            self.client, DUMMY_ENDPOINT + "/5b07f6ef48e7553a10c05ab7",
            [{'dummy': True}])
        assert response.status_code == 400

    def test_put_id_in_body_not_allowed(self):
        response = put_json(
            self.client, DUMMY_ENDPOINT + "/5b07f6ef48e7553a10c05ab7",
            {'_id': 1, 'dummy': False})
        assert response.status_code == 422


class ModifyTestCase(unittest.TestCase):
    def setUp(self):
        set_up(self)
        delete_database(self.db_client, DUMMY_DOMAIN)
        response = post_json(self.client, DUMMY_ENDPOINT,
                             [{'dummy': True, 'second': True}])
        self.dummy_entry_id = response.location.split('/')[-1]
        assert response.status_code == 201

    def tearDown(self):
        self.app_context.pop()
        delete_database(self.db_client, DUMMY_DOMAIN)

    def test_patch_domain(self):
        response = patch_json(self.client, DUMMY_DOMAIN,
                              [{'dummy': False}])
        assert response.status_code == 405

    def test_patch_nonexisting_domain(self):
        response = patch_json(self.client, DUMMY_DOMAIN,
                              [{'dummy': False}])
        assert response.status_code == 405

    def test_patch_model(self):
        response = patch_json(self.client, DUMMY_ENDPOINT,
                              [{'dummy': False}])
        assert response.status_code == 405

    def test_patch_nonexisting_model(self):
        response = patch_json(self.client, DUMMY_ENDPOINT,
                              [{'dummy': False}])
        assert response.status_code == 405

    def test_patch_modifies_entry(self):
        response = patch_json(
            self.client, DUMMY_ENDPOINT + '/' + self.dummy_entry_id,
            {'dummy': False})
        assert response.status_code == 200
        response = self.client.get(DUMMY_ENDPOINT + '/' + self.dummy_entry_id)
        assert json_of_response(response) == {'_id': self.dummy_entry_id,
                                              'dummy': False, 'second': True}

    def test_patch_nonexisting_id_entity(self):
        response = patch_json(
            self.client, DUMMY_ENDPOINT + "/5b07f6ef48e7553a10c05ab7",
            {'dummy': False})
        assert response.status_code == 404

    def test_patch_expect_single_json_get_list(self):
        response = patch_json(
            self.client, DUMMY_ENDPOINT + "/1", [{'second': True}])
        assert response.status_code == 400

    def test_patch_id_in_body(self):
        response = patch_json(
            self.client, DUMMY_ENDPOINT + '/' + self.dummy_entry_id,
            {'_id': self.dummy_entry_id, 'dummy': False})
        assert response.status_code == 422


if __name__ == '__main__':
    unittest.main()

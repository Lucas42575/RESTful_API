from flask import jsonify


def success(code, message, count=0, location=None, link=None):
    response = jsonify({'info': message, 'count': count})
    response.status_code = code
    if location:
        response.headers['location'] = location
    if link:
        response.headers['link'] = link
    return response


def register_error_handlers(app):

    @app.errorhandler(400)
    def bad_request(error):
        response = jsonify({
            'error': 'bad request',
            'message': error.description})
        response.status_code = 400
        return response

    @app.errorhandler(403)
    def forbidden(error):
        response = jsonify({
            'error': 'forbidden',
            'message': error.description})
        response.status_code = 403
        return response

    @app.errorhandler(404)
    def not_found(error):
        response = jsonify({
            'error': 'not found',
            'message': error.description})
        response.status_code = 404
        return response

    @app.errorhandler(405)
    def method_not_allowed(error):
        response = jsonify({
            'error': 'method not allowed',
            'message': error.description})
        response.status_code = 405
        return response

    @app.errorhandler(422)
    def unprocessable_entity(error):
        response = jsonify({
            'error': 'unprocessable entity',
            'message': error.description})
        response.status_code = 422
        return response

"""
Contains all of the /api/unique/* routes added by this plugin.
"""

import io

from flask import request, send_file, abort
from flask_restplus import Namespace, Resource
from CTFd.models import db
from CTFd.utils.decorators import admins_only
from CTFd.utils.dates import ctftime
from CTFd.utils.user import is_admin

from .models import UniqueChallengeFiles, UniqueChallenges, UniqueChallengeScript
from .helpers import get_unique_challenge_file, get_generated_challenge_file
from .lispish import LispIsh, LispIshParseError

API_NAMESPACE = Namespace("unique", description="API endpoint for unique challenges")

@API_NAMESPACE.route("/files")
class Files(Resource):
    """ Allows users to upload unique files. """
    @admins_only
    def post(self):
        """ Handle the post request. """
        data = request.form or request.get_json()
        challenge_id = data.get('challenge')
        uploads = []

        for file in request.files.getlist('file'):
            upload = UniqueChallengeFiles(
                name=file.filename,
                content=file.stream.read(),
                challenge_id=challenge_id
            )
            db.session.add(upload)
            uploads.append(upload)
        db.session.commit()

        return {
            "success": True,
            "data": [dict(name=u.name, id=u.id) for u in uploads]
        }

@API_NAMESPACE.route("/files/<challenge_id>")
@API_NAMESPACE.param("challenge_id", "A challenge ID")
class ChallengeFiles(Resource):
    """ Allow users to get a list of challenge files for a given challenge. """
    def get(self, challenge_id):
        """ Handle the get request """
        if not is_admin() and not ctftime():
            abort(403)
        files = UniqueChallengeFiles.query.filter_by(challenge_id=challenge_id).all()
        return {
            "success": True,
            "data": [dict(name=f.name, id=f.id) for f in files]
        }

@API_NAMESPACE.route("/files/<challenge_id>/<file_id>")
@API_NAMESPACE.param("challenge_id", "A challenge ID")
@API_NAMESPACE.param("file_id", "A file ID")
class ChallengeFile(Resource):
    """ Allow admins to download a given challenge file """
    def get(self, challenge_id, file_id):
        """ Handle the get request """
        if not is_admin() and not ctftime():
            abort(403)

        challenge = UniqueChallenges.query.filter_by(id=challenge_id).first_or_404()
        file = (UniqueChallengeFiles.query.filter_by(challenge_id=challenge_id, id=file_id)
                .first_or_404())
        return send_file(
            io.BytesIO(get_unique_challenge_file(challenge, file.content)),
            attachment_filename=file.name,
            as_attachment=True,
            mimetype='application/octet-stream'
        )

    @admins_only
    def delete(self, challenge_id, file_id):
        """ Handle the delete request """
        UniqueChallengeFiles.query.filter_by(challenge_id=challenge_id, id=file_id).delete()
        db.session.commit()
        return {"success": True}


@API_NAMESPACE.route("/generated-files")
class GeneratedFiles(Resource):
    """ Allows admins to create unique file scripts. """
    @admins_only
    def post(self):
        """ Handle the post request. """
        data = request.form or request.get_json()
        challenge_id = data.get('challenge')
        if data.get('id'):
            script = UniqueChallengeScript.query.filter_by(id=data.get('id')).one()
            script.name = data.get('name')
            script.script = bytes(data.get('script'), 'utf-8')
        else:
            script = UniqueChallengeScript(
                name=data.get('name'),
                script=bytes(data.get('script'), 'utf-8'),
                challenge_id=challenge_id
            )
            db.session.add(script)
        db.session.commit()

        return {
            "success": True,
            "created": not data.get('id'),
            "name": script.name,
            "id": script.id
        }

@API_NAMESPACE.route("/generated-files/<challenge_id>")
@API_NAMESPACE.param("challenge_id", "A challenge ID")
class GeneratedChallengeFiles(Resource):
    """ Allow users to get a list of generated challenge files for a given challenge. """
    def get(self, challenge_id):
        """ Handle the get request """
        if not is_admin() and not ctftime():
            abort(403)
        files = UniqueChallengeScript.query.filter_by(challenge_id=challenge_id).all()
        return {
            "success": True,
            "data": [dict(name=f.name, id=f.id) for f in files]
        }

@API_NAMESPACE.route("/generated-files/<challenge_id>/<file_id>")
@API_NAMESPACE.param("challenge_id", "A challenge ID")
@API_NAMESPACE.param("file_id", "A file ID")
class GeneratedChallengeFile(Resource):
    """ Allow admins to view/delete a given generated challenge file """
    @admins_only
    def get(self, challenge_id, file_id):
        """ Handle the get request """
        challenge = UniqueChallenges.query.filter_by(id=challenge_id).first_or_404()
        file = (UniqueChallengeScript.query.filter_by(challenge_id=challenge_id, id=file_id)
                .first_or_404())
        return dict(success=True, name=file.name, script=file.script.decode('utf-8'), id=file.id)

    @admins_only
    def delete(self, challenge_id, file_id):
        """ Handle the delete request """
        UniqueChallengeScript.query.filter_by(challenge_id=challenge_id, id=file_id).delete()
        db.session.commit()
        return {"success": True}

@API_NAMESPACE.route("/generated-files/<challenge_id>/<file_id>/download")
@API_NAMESPACE.param("challenge_id", "A challenge ID")
@API_NAMESPACE.param("file_id", "A file ID")
class GeneratedChallengeFileDownload(Resource):
    """ Allow users to download a given generated challenge file """
    def get(self, challenge_id, file_id):
        """ Handle the get request """
        if not is_admin() or not ctftime():
            abort(403)
        challenge = UniqueChallenges.query.filter_by(id=challenge_id).first_or_404()
        file = (UniqueChallengeScript.query.filter_by(challenge_id=challenge_id, id=file_id)
                .first_or_404())
        return send_file(
            io.BytesIO(get_generated_challenge_file(challenge, file.script.decode('utf-8'))),
            attachment_filename=file.name,
            as_attachment=True,
            mimetype='application/octet-stream'
        )

@API_NAMESPACE.route("/lispish/parse")
class LispIshData(Resource):
    """ Helper to allow users to check that the given lispish is valid. """
    def post(self):
        """ Check the submitted code and let the user know if it is valid. """
        data = request.form or request.get_json()
        code = data.get('code')
        if not code or not isinstance(code, str):
            return dict(
                success=False,
                error="You must provide the code parameter with code to try to parse."
            )
        try:
            parsed = LispIsh().parse(code)
            return dict(success=True, emitted=parsed.emit())
        except LispIshParseError as error:
            return dict(success=False, error=str(error))

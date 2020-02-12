import io

from flask import request, send_file
from flask_restplus import Namespace, Resource
from CTFd.cache import clear_standings
from CTFd.models import db, Awards
from CTFd.schemas.awards import AwardSchema
from CTFd.utils.decorators import admins_only
from CTFd.utils.dates import ctftime
from CTFd.utils.user import is_admin

from .models import UniqueChallengeFiles, UniqueChallenges
from .helpers import get_unique_challenge_file

api_namespace = Namespace("unique", description="API endpoint for unique challenges")

@api_namespace.route("/files")
class Files(Resource):
    @admins_only
    def post(self):
        data = request.form or request.get_json()
        challenge_id = data.get('challenge')
        uploads = []

        for file in request.files.getlist('file'):
            upload = UniqueChallengeFiles(
                name = file.filename,
                content = file.stream.read(),
                challenge_id = challenge_id
            )
            db.session.add(upload)
            uploads.append(upload)
        db.session.commit()

        return {
            "success": True,
            "data": [ dict(name=u.name, id=u.id) for u in uploads ]
        }

@api_namespace.route("/files/<challenge_id>")
@api_namespace.param("challenge_id", "A challenge ID")
class ChallengeFiles(Resource):
    def get(self, challenge_id):
        if not is_admin() and not ctftime():
            abort(403)
        files = UniqueChallengeFiles.query.filter_by(challenge_id=challenge_id).all()
        return {
            "success": True,
            "data": [ dict(name=f.name, id=f.id) for f in files ]
        }

@api_namespace.route("/files/<challenge_id>/<file_id>")
@api_namespace.param("challenge_id", "A challenge ID")
@api_namespace.param("file_id", "A file ID")
class ChallengeFile(Resource):
    def get(self, challenge_id, file_id):
        if not is_admin() and not ctftime():
            abort(403)

        challenge = UniqueChallenges.query.filter_by(id=challenge_id).first_or_404()
        file = UniqueChallengeFiles.query.filter_by(challenge_id=challenge_id, id=file_id).first_or_404()
        return send_file(
            io.BytesIO(get_unique_challenge_file(challenge, file.content)),
            attachment_filename=file.name,
            as_attachment=True,
            mimetype='application/octet-stream'
        )

    @admins_only
    def delete(self, challenge_id, file_id):
        UniqueChallengeFiles.query.filter_by(challenge_id=challenge_id, id=file_id).delete()
        return { "success": True }

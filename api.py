"""
Contains all of the /api/unique/* routes added by this plugin.
"""

import io

from flask import request, send_file, abort
from sqlalchemy import text
from flask_restplus import Namespace, Resource
from CTFd.models import db, Submissions, Users, Teams
from CTFd.utils import set_config
from CTFd.utils.decorators import admins_only
from CTFd.utils.dates import ctftime
from CTFd.utils.user import is_admin

from .models import UniqueChallengeFiles, UniqueChallenges, UniqueChallengeScript, UniqueChallengeRequirements, UniqueFlags
from .helpers import get_unique_challenge_file, get_generated_challenge_file, meets_advanced_requirements
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
        if not meets_advanced_requirements(challenge_id):
            return dict(success=True, data=[])
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
        if not meets_advanced_requirements(challenge_id):
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
        if not meets_advanced_requirements(challenge_id):
            return dict(success=True, data=[])
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
        if not is_admin() and not ctftime():
            abort(403)
        if not meets_advanced_requirements(challenge_id):
            return abort(403)
        challenge = UniqueChallenges.query.filter_by(id=challenge_id).first_or_404()
        file = (UniqueChallengeScript.query.filter_by(challenge_id=challenge_id, id=file_id)
                .first_or_404())
        return send_file(
            io.BytesIO(get_generated_challenge_file(challenge, file.script.decode('utf-8'))),
            attachment_filename=file.name,
            as_attachment=True,
            mimetype='application/octet-stream'
        )

@API_NAMESPACE.route("/requirements/<challenge_id>")
@API_NAMESPACE.param("challenge_id", "A challenge ID")
class UniqueChallengeRequirementsResource(Resource):
    @admins_only
    def get(self, challenge_id):
        """ Get the script for editing """
        requirement = UniqueChallengeRequirements.query.filter_by(challenge_id=challenge_id).first()
        return {
            'status': 'ok',
            'script': requirement.script.decode('utf-8') if requirement else ''
        }

    @admins_only
    def post(self, challenge_id):
        """ Save the given requirements """
        requirement = UniqueChallengeRequirements.query.filter_by(challenge_id=challenge_id).first()
        if not requirement:
            requirement = UniqueChallengeRequirements(challenge_id=challenge_id)
            db.session.add(requirement)

        data = request.form or request.get_json()
        script = data.get('script')
        if script is None or script == '':
            script = ''
        else:
            try:
                script = LispIsh().parse(script).emit()
            except LispIshParseError as error:
                return dict(status='error', error=str(error))
        requirement.script = bytes(script, 'utf-8')
        db.session.commit()
        return dict(status='ok', script=requirement.script.decode('utf-8'))

@API_NAMESPACE.route("/config")
class UniqueChallengesConfig(Resource):
    @admins_only
    def post(self):
        data = request.form or request.get_json()
        set_config("unique_challenges_filter_list", bool(data.get("filter_list")))
        return dict(status='ok')

@API_NAMESPACE.route("/audit")
class AuditList(Resource):
    """ Provides a list of users along with high level audit info. """
    @admins_only
    def get(self):
        # First get all submissions that are suspect. These are submissions which
        # include a unique flag for that challenge but are marked incorrect.
        # TODO: SQLAlchemy surely has some way to represent this via the query builder
        # but I gave up and just used text after an hour banging my head against it...
        statement = text("""
            SELECT s.challenge_id, s.id, s.user_id, s.team_id, uf.user_id as ufuid, uf.team_id as uftid FROM submissions AS s
            JOIN unique_flags AS uf
                ON uf.challenge_id = s.challenge_id
                WHERE type = "incorrect"
                AND (
                    INSTR(s.provided, uf.flag_8)
                    OR INSTR(s.provided, uf.flag_16)
                    OR INSTR(s.provided, uf.flag_32)
                )
                AND (
                    (uf.user_id IS NULL OR uf.user_id <> s.user_id)
                    AND (uf.team_id IS NULL OR uf.team_id <> s.team_id)
                )
        """)
        # NOTE: We request specific columns here instead of the Submissions/UniqueFlags object because
        # SQLAlchemy dedupes - https://docs.sqlalchemy.org/en/13/faq/sessions.html#faq-query-deduplicating
        query = db.session.query(
            Submissions.challenge_id, Submissions.id,
            Submissions.user_id, Submissions.team_id,
            UniqueFlags.user_id.label('ufuid'), UniqueFlags.team_id.label('uftid')
        ).from_statement(statement)

        suspect = []
        users = set()
        teams = set()
        for (c_id, sub_id, sub_uid, sub_tid, uf_uid, uf_tid) in query:
            users.add(sub_uid)
            users.add(uf_uid)
            teams.add(sub_tid)
            teams.add(uf_tid)

            challenge = UniqueChallenges.query.filter_by(id=c_id).one()
            suspect.append(dict(
                challenge_id=challenge.id,
                submission_id=sub_id,
                challenge_name=challenge.name,
                team_id=sub_tid,
                source_team=uf_tid,
                user_id=sub_uid,
                source_user=uf_uid
            ))

        users_arr = []
        for user in users:
            if user is None:
                continue
            db_user = Users.query.filter_by(id=user).one()
            users_arr.append(dict(id=db_user.id, name=db_user.name))

        teams_arr = []
        for team in teams:
            if team is None:
                continue
            db_team = Teams.query.filter_by(id=team).one()
            teams_arr.append(dict(id=db_team.id, name=db_team.name))

        return dict(
            status='ok',
            suspect=suspect,
            users=users_arr,
            teams=teams_arr
        )

"""
Registers the unique challenges plugin with CTFd.
"""

from flask import Blueprint
from flask_restplus import Api

from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.flags import get_flag_class
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge, CTFdStandardChallenge
from CTFd.models import (
    db,
    Solves,
    Fails,
    Flags,
    Challenges,
    ChallengeFiles,
    Tags,
    Hints,
)
from CTFd.utils.user import get_ip
from CTFd.utils.uploads import delete_file
from CTFd.utils.decorators import admins_only

from .models import UniqueFlags, UniqueChallenges, UniqueChallengeFiles
from .helpers import get_unique_challenge_description, replace_submission
from .api import API_NAMESPACE

class UniqueChallenge(BaseChallenge):
    """ Defines a unique challenge type, where users will be given challenges
    that contain unique flags per user/team. """
    id = "unique"  # Unique identifier used to register challenges
    name = "unique"  # Name of a challenge type
    templates = {  # Templates used for each aspect of challenge editing & viewing
        "create": "/plugins/unique_challenges/assets/create.html",
        "update": "/plugins/unique_challenges/assets/update.html",
        "view": "/plugins/unique_challenges/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/unique_challenges/assets/create.js",
        "update": "/plugins/unique_challenges/assets/update.js",
        "view": "/plugins/unique_challenges/assets/view.js",
    }

    @staticmethod
    def create(request):
        """ Create a new unique challenge """
        data = request.form or request.get_json()
        challenge = UniqueChallenges(**data)
        db.session.add(challenge)
        db.session.commit()
        return challenge

    @staticmethod
    def read(challenge):
        """ Read the challenge into a JSON-serializable object to send to the frontend """
        challenge = UniqueChallenges.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "description": get_unique_challenge_description(challenge),
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": UniqueChallenge.id,
                "name": UniqueChallenge.name,
                "templates": UniqueChallenge.templates,
                "scripts": UniqueChallenge.scripts,
            },
        }
        return data

    @staticmethod
    def update(challenge, request):
        """ Handle the challenge update request """
        data = request.form or request.get_json()
        for attr, value in data.items():
            setattr(challenge, attr, value)

        db.session.commit()
        return challenge

    @staticmethod
    def delete(challenge):
        """ Handle the challenge delete request """
        files = ChallengeFiles.query.filter_by(challenge_id=challenge.id).all()
        for file in files:
            delete_file(file.id)
        UniqueChallengeFiles.query.filter_by(challenge_id=challenge.id).delete()

        tables = [
            Fails,
            Solves,
            UniqueFlags,
            Flags,
            ChallengeFiles,
            Tags,
            Hints
        ]

        for table in tables:
            table.query.filter_by(challenge_id=challenge.id).delete()
        for table in [UniqueChallenges, Challenges]:
            table.query.filter_by(id=challenge.id).delete()

        db.session.commit()

    @staticmethod
    def attempt(challenge, request):
        """ Called when a user tries to complete a challenge """
        data = request.form or request.get_json()
        cheating, submission = replace_submission(challenge, data["submission"].strip())

        if cheating:
            return False, "Incorrect"

        flags = Flags.query.filter_by(challenge_id=challenge.id).all()
        for flag in flags:
            if get_flag_class(flag.type).compare(flag, submission):
                return True, "Correct"
        return False, "Incorrect"

    solve = CTFdStandardChallenge.solve
    fail = CTFdStandardChallenge.fail

def load(app):
    """ Load the unique challenges plugin """

    app.db.create_all()
    CHALLENGE_CLASSES["unique"] = UniqueChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/unique_challenges/assets/")

    blueprint = Blueprint("unique_api", __name__)
    api = Api(blueprint)
    api.add_namespace(API_NAMESPACE, "/unique")
    app.register_blueprint(blueprint, url_prefix="/api")

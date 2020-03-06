"""
Registers the unique challenges plugin with CTFd.
"""

from flask import Blueprint, render_template
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
from CTFd.utils import get_config
from CTFd.utils.user import get_ip
from CTFd.utils.uploads import delete_file
from CTFd.utils.decorators import admins_only

from .models import UniqueFlags, UniqueChallenges, UniqueChallengeFiles
from .helpers import get_unique_challenge_description, replace_submission, meets_advanced_requirements
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
        # Advanced requirements don't need to be handled here. They are handled by the overwritten route.
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

        if not meets_advanced_requirements(challenge.id):
            return False, "Missing requirements"

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

    api_blueprint = Blueprint("unique_api", __name__)
    plugin_blueprint = Blueprint("unique_plugin", __name__, template_folder="assets")

    @plugin_blueprint.route("/admin/unique_challenges")
    @admins_only
    def configure_route():
        return render_template(
            "unique_challenges.html",
            filter_list=get_config("unique_challenges_filter_list", False)
        )

    api = Api(api_blueprint)
    api.add_namespace(API_NAMESPACE, "/unique")
    app.register_blueprint(api_blueprint, url_prefix="/api")
    app.register_blueprint(plugin_blueprint)

    # Overwrite /api/v1/challenges
    old_challenges_list = app.view_functions['api.challenges_challenge_list']
    def challenges_list(*args, **kwargs):
        result = old_challenges_list(*args, **kwargs)
        if get_config("unique_challenges_filter_list", False):
            result.json['data'] = [
                challenge for challenge in result.json['data'] if meets_advanced_requirements(challenge['id'])
            ]
            return result.json
        return result
    app.view_functions['api.challenges_challenge_list'] = challenges_list

    # Overwrite /api/v1/challenges/<challenge_id>
    old_challenges_view = app.view_functions['api.challenges_challenge']
    def challenges_view(*args, **kwargs):
        result = old_challenges_view(*args, **kwargs)
        if not meets_advanced_requirements(result.json['data']['id']):
            result.json['data']['state'] = 'missing-requirements'
            result.json['data']['description'] = "You don't meet the requirements to complete this challenge."
            result.json['data']['files'] = None
            return result.json
        return result
    app.view_functions['api.challenges_challenge'] = challenges_view

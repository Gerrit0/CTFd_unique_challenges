from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.flags import get_flag_class
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
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

from .models import UniqueFlags, UniqueChallenges
from .helpers import get_unique_challenge_description, replace_submission

class UniqueChallenge(BaseChallenge):
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
        data = request.form or request.get_json()
        challenge = UniqueChallenges(**data)
        db.session.add(challenge)
        db.session.commit()
        return challenge

    @staticmethod
    def read(challenge):
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
        data = request.form or request.get_json()
        for attr, value in data.items():
            setattr(challenge, attr, value)

        db.session.commit()
        return challenge

    @staticmethod
    def delete(challenge):
        files = ChallengeFiles.query.filter_by(challenge_id=challenge.id).all()
        for f in files:
            delete_file(f.id)

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
        data = request.form or request.get_json()
        cheating, submission = replace_submission(challenge, data["submission"].strip())

        if cheating:
            return False, "Incorrect"

        flags = Flags.query.filter_by(challenge_id=challenge.id).all()
        for flag in flags:
            if get_flag_class(flag.type).compare(flag, submission):
                return True, "Correct"
        return False, "Incorrect"

    @staticmethod
    def solve(user, team, challenge, request):
        """Copied directly from the standard challenge. 
        Nothing special here.
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        solve = Solves(
            user_id=user.id,
            team_id=team.id if team else None,
            challenge_id=challenge.id,
            ip=get_ip(req=request),
            provided=submission,
        )
        db.session.add(solve)
        db.session.commit()
        db.session.close()

    @staticmethod
    def fail(user, team, challenge, request):
        """Copied directly from the standard challenge.
        Nothing special here.
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        wrong = Fails(
            user_id=user.id,
            team_id=team.id if team else None,
            challenge_id=challenge.id,
            ip=get_ip(request),
            provided=submission,
        )
        db.session.add(wrong)
        db.session.commit()
        db.session.close()

def load(app):
    app.db.create_all()
    CHALLENGE_CLASSES["unique"] = UniqueChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/unique_challenges/assets/")

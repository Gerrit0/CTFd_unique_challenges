import re
from secrets import token_hex

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
from CTFd.utils import config
from CTFd.utils.user import get_ip, get_current_user, get_current_team, is_admin
from CTFd.utils.uploads import delete_file
from flask import abort
from .models import UniqueFlags, UniqueChallenges

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
        unique_flags = UniqueChallenge._ensure_flags_for_challenge(challenge.id)
        challenge = UniqueChallenges.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "description": UniqueChallenge._replace_challenge(challenge.description, unique_flags, get_current_user().name),
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
        unique_flags = UniqueChallenge._ensure_flags_for_challenge(challenge.id)
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        submission = UniqueChallenge._replace_submission(
            submission, unique_flags, get_current_user().name
        )

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

    @staticmethod
    def _ensure_flags_for_challenge(challenge_id):
        user = get_current_user()
        if not user:
            abort(401) # Unauthorized
        if config.is_teams_mode():
            team = get_current_team()
            if not team:
                abort(401)
            result = UniqueFlags.query.filter_by(
                challenge_id=challenge_id,
                team_id=team.id
            ).first()
        else:
            result = UniqueFlags.query.filter_by(
                challenge_id=challenge_id,
                user_id=user.id
            ).first()

        if result is None: # Missing, insert new unique flags
            result = UniqueFlags(
                challenge_id = challenge_id,
                user_id = user.id,
                team_id = get_current_team().id if config.is_teams_mode() else None,
                flag_8 = token_hex(4),
                flag_16 = token_hex(8),
                flag_32 = token_hex(16)
            )
            db.session.add(result)
            db.session.commit()
        return result

    @staticmethod
    def _replace_challenge(challenge, unique_flags, username):
        """The inverse of replace_submission, without the need to worry about
        malicious input.
        """
        if is_admin():
            return challenge
        regex = re.compile(r"!name!|!flag_8!|!flag_16!|!flag_32!")
        return regex.sub(
            lambda match: username if match.group(0) == "!name!"
                else getattr(unique_flags, match.group(0)[1:-1]),
            challenge
        )

    @staticmethod
    def _replace_submission(submission, unique_flags, username):
        """Normalizes the submission so that static flags can include the placeholders.
        Note that to avoid participants being able to submit placeholders to complete
        challenges we also have to replace the placeholders in the submission with an invalid
        value. Currently, this is set to the empty string.
        """
        replacements = {
            "!name!": "",
            "!flag_8!": "",
            "!flag_16": "",
            "!flag_32": "",
            username: "!user!",
            unique_flags.flag_8: "!flag_8!",
            unique_flags.flag_16: "!flag_16!",
            unique_flags.flag_32: "!flag_32!"
        }
        regex = re.compile("|".join(map(re.escape, replacements)))
        return regex.sub(lambda match: replacements[match.group(0)], submission)

def load(app):
    app.db.create_all()
    CHALLENGE_CLASSES["unique"] = UniqueChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/unique_challenges/assets/")

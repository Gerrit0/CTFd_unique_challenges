"""
Contains helper functions for working with the challenge flags.
"""

import sys
from io import TextIOWrapper, BytesIO
import re
from secrets import token_hex
from flask import abort

from CTFd.utils.user import get_current_user, get_current_team, is_admin
from CTFd.utils import config
from CTFd.models import db

from .models import UniqueFlags


def get_flags_for_challenge(challenge_id):
    """ Assumes the user already has unique flags created by
    ensure_flags_for_challenge."""
    if config.is_teams_mode():
        return UniqueFlags.query.filter_by(
            challenge_id=challenge_id,
            team_id=get_current_team().id
        ).first()
    else:
        return UniqueFlags.query.filter_by(
            challenge_id=challenge_id,
            user_id=get_current_user().id
        ).first()


def ensure_flags_for_challenge(challenge_id, also_admins=False):
    """ Makes sure that there is a flag for the given challenge
    and current user. Will not create flags if the user is an admin unless also_admins is true. """
    # Admins don't get flags, their input is passed through without
    # replacement.
    if is_admin() and not also_admins:
        return
    user = get_current_user()
    if not user:
        abort(401) # Unauthorized
    if config.is_teams_mode() and not get_current_team():
        abort(401) # Cannot complete challenge, so don't create flags

    if config.is_teams_mode():
        flags = UniqueFlags.query.filter_by(
            challenge_id=challenge_id,
            team_id=get_current_team().id
        ).first()
    else:
        flags = UniqueFlags.query.filter_by(
            challenge_id=challenge_id,
            user_id=user.id
        ).first()

    if not flags: # Missing, insert new flags
        flags = UniqueFlags(
            challenge_id=challenge_id,
            user_id=user.id if not config.is_teams_mode() else None,
            team_id=get_current_team().id if config.is_teams_mode() else None,
            flag_8=token_hex(4),
            flag_16=token_hex(8),
            flag_32=token_hex(16)
        )
        db.session.add(flags)
        db.session.commit()

def get_unique_challenge_description(challenge):
    """ Replaces the challenge description with the unique flags for the given
    user, or the raw challenge if the user is an admin.
    Returns the (maybe) modified challenge description.
    """
    if is_admin():
        return challenge.description
    ensure_flags_for_challenge(challenge.id)
    username = get_current_user().name
    unique_flags = get_flags_for_challenge(challenge.id)
    regex = re.compile(r"!name!|!flag_8!|!flag_16!|!flag_32!")
    return regex.sub(
        lambda match: username if match.group(0) == "!name!"
        else getattr(unique_flags, match.group(0)[1:-1]),
        challenge.description
    )

def get_unique_challenge_file(challenge, content):
    """ Replaces placeholders in the given content for the current user
    or returns the raw content if the user is an admin.
    """
    if is_admin():
        return content
    ensure_flags_for_challenge(challenge.id)
    username = get_current_user().name
    unique_flags = get_flags_for_challenge(challenge.id)
    regex = re.compile(rb"!name!|!flag_8!|!flag_16!|!flag_32!")
    return regex.sub(
        lambda match: bytes(username, 'ascii') if match.group(0) == b"!name!"
        else bytes(getattr(unique_flags, match.group(0)[1:-1].decode('utf-8')), 'ascii'),
        content
    )

def replace_submission(challenge, submission):
    """ Normalizes the submission so that static flags can include
    the placeholders to allow participants to complete the challenge.
    Returns a tuple (cheating, submission) in which cheating is true
    if the user tries to include a placeholder in their submission.
    If cheating is true, the submission should not be checked against
    any flags."""
    # Admins don't get unique flags, pass their input directly through.
    if is_admin():
        return False, submission

    # Check for cheating.
    placeholders = ['!name!', '!flag_8!', '!flag_16!', '!flag_32!']
    if any([p in submission for p in placeholders]):
        return True, None

    ensure_flags_for_challenge(challenge.id)
    unique_flags = get_flags_for_challenge(challenge.id)
    replacements = {
        get_current_user().name: "!name!",
        unique_flags.flag_8: "!flag_8!",
        unique_flags.flag_16: "!flag_16!",
        unique_flags.flag_32: "!flag_32!"
    }
    regex = re.compile("|".join(map(re.escape, replacements)))
    return False, regex.sub(lambda match: replacements[match.group(0)], submission)

class CaptureExec:
    """ Helper class to wrap user scripts that print to stdout.
    """
    def __init__(self, script: str):
        self._script = script

    def run(self, local_vars={}) -> str:
        # Setup, capture stdout
        old, sys.stdout = sys.stdout, TextIOWrapper(
            BytesIO(), sys.stdout.encoding)
        # Run user script, note that builtins are enabled. Untrusted input
        # should not be passed to this function.
        try:
            exec(self._script, {}, local_vars)
        except Exception as e:
            print("ERROR CREATING FILE: CONTACT AN ADMINISTRATOR")
            print("Exception when running admin code to generate a file:", file=sys.stderr)
            print(e, file=sys.stderr)
        # Get the output
        sys.stdout.seek(0)
        out = sys.stdout.read()
        sys.stdout.close()
        sys.stdout = old
        return out

def get_generated_challenge_file(challenge, script: str) -> bytes:
    """ Calls an administrator provided script to generate content for the given user"""
    # Even admins get flags for challenge files... There's a separate route for editing.
    ensure_flags_for_challenge(challenge.id, True)
    flags = get_flags_for_challenge(challenge.id)
    placeholders = dict(
        flag_8=flags.flag_8,
        flag_16=flags.flag_16,
        flag_32=flags.flag_32,
        name=get_current_user().name
    )
    capture = CaptureExec(script)
    return bytes(capture.run(dict(PLACEHOLDERS=placeholders)), 'utf-8')

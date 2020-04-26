"""
Contains all of the models added by this plugin.
"""

from CTFd.models import db, Challenges

class UniqueFlags(db.Model):
    """ Unlike the standard flags, each unique challenge gets a set of three unique flags.
    These flags can be injected into the challenge text and will be transformed back into
    the placeholders on submission.
    """
    __tablename__ = "unique_flags"
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE")
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE")
    )
    team_id = db.Column(
        db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE")
    )
    flag_8 = db.Column(db.String(8))
    flag_16 = db.Column(db.String(16))
    flag_32 = db.Column(db.String(32))

    user = db.relationship("Users", foreign_keys="UniqueFlags.user_id", lazy="select")
    team = db.relationship("Teams", foreign_keys="UniqueFlags.team_id", lazy="select")

    def __repr__(self):
        return f"<UniqueFlag {self.id} for challenge {self.challenge_id}>"


class UniqueChallenges(Challenges):
    """ Required for CTFd, even though there is no difference from the standard challenge.
    """
    __mapper_args__ = {'polymorphic_identity': 'unique'}
    id = db.Column(None, db.ForeignKey('challenges.id'), primary_key=True)


class UniqueChallengeFiles(db.Model):
    """ Represents a file whose contents will be replaced when a user downloads it.
    """
    __tablename__ = "unique_files"
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE")
    )
    name = db.Column(db.String(64))
    content = db.Column(db.BLOB)

    def __repr__(self):
        return f"<UniqueChallengeFile {self.id} {self.name} for challenge {self.challenge_id}>"

class UniqueChallengeScript(db.Model):
    """ Represents a python script provided by an administrator that will use the placeholders
    to generate a file for a given user.
    """
    __tablename__ = "unique_scripts"
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE")
    )
    name = db.Column(db.String(64))
    script = db.Column(db.BLOB)

class UniqueChallengeRequirements(db.Model):
    """ Represents a LispIsh script provided by an administrator that determines
    if the given challenge can be completed by a user.
    """
    __tablename__ = "unique_requirements"
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE")
    )
    script = db.Column(db.BLOB)

class UniqueChallengeCohort(db.Model):
    """ Represents a group of users created by an administrator. """
    __tablename__ = "unique_cohorts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

class UniqueChallengeCohortMembership(db.Model):
    """ Represents a user's membership to a cohort """
    __tablename__ = "unique_cohorts_members"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE")
    )
    cohort_id = db.Column(
        db.Integer, db.ForeignKey("unique_cohorts.id", ondelete="CASCADE")
    )

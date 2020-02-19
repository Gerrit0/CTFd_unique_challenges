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

    def __repr__(self):
        return f"<UniqueFlag {self.content} for challenge {self.challenge_id}>"


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

"""
Creates the demo challenges + users.
Note: This assumes the ctf is set up in users mode.
"""
# Fix import paths... Feels like this ought not be necessary, but I don't really
# understand how python imports work.
import sys
from os.path import join, dirname, abspath
sys.path.append(abspath(join(dirname(__file__), '..', '..', '..')))

import random
from secrets import token_hex
from collections import defaultdict

from CTFd import create_app
from CTFd.models import db, Flags, Users, Solves, Fails, Submissions

from CTFd.plugins.unique_challenges.models import (
    UniqueChallenges,
    UniqueChallengeFiles,
    UniqueChallengeScript,
    UniqueChallengeRequirements,
    UniqueFlags,
    UniqueChallengeCohort,
    UniqueChallengeCohortMembership,
)

app = create_app()

challenges = [
    {
        "name": "Enter your name",
        "description": """Complete this challenge by entering your username as the flag.

This could be used to ask students to sign their name agreeing not to cheat or just for a simple flag

Flag: !name!""",
        "value": 5
    },
    {
        "name": "Grep",
        "description": """To complete this challenge you will need to use [grep](http://man7.org/linux/man-pages/man1/grep.1.html).

Download grep.txt and run the following command to get your flag.
```bash
grep -v "not this line" grep.txt
```""",
        "value": 10
    },
    {
        "name": "Python",
        "description": """Download and run the given python file to get your flag!

This is just a demonstration that the file type doesn't matter.""",
        "value": 10
    },
    {
        "name": "Caesar Cipher",
        "description": """This challenge demonstrates the use of script files to generate custom content via a administrator-provided script.

To solve the challenge, download caesar.txt and decode its contents with a Caesar-cipher tool. The simple one at https://www.xarg.org/tools/caesar-cipher/ with the default shift of 13 will work.

To check your work - the result should be: !flag_32!""",
        "value": 13
    },
    {
        "name": "Who listens in on Alice and Bob?",
        "description": """[Alice and Bob](https://en.wikipedia.org/wiki/Alice_and_Bob) are common placeholder names in cryptology. Alice wants to send a message to Bob, but Eve (you!) wants to listen in.

Your flag is: !flag_8!

Don't forget to change your name back to your usual name after completing the challenge.""",
        "value": 20
    }
]

flags = [
    ("Enter your name", "!name!"),
    ("Grep", "!flag_8!"),
    ("Python", "!flag_8!"),
    ("Caesar Cipher", "!flag_32!"),
    ("Who listens in on Alice and Bob?", "!flag_8!")
]

files = [
    ("Grep", "grep.txt", "not this line\n" * 1234 + "!flag_8!\n" + "not this line!\n" * 2311),
    ("Python", "script.py", '''text = """
This just demonstrates that the file type doesn't matter.
Flags will be replaced everywhere.

Your flag is !flag_8!
"""

if __name__ == '__main__':
    print(text)''')
]

scripts = [
    ("Caesar Cipher", "caesar.txt", """# PLACEHOLDERS is provided by the unique_challenges plugin when evaling this code
# PLACHOLDERS = dict(flag_8='a'*8, flag_16='b'*16, flag_32='c'*32, name='name')
def caesar(plaintext, shift):
    import string
    alphabet = string.ascii_lowercase
    shifted_alphabet = alphabet[shift:] + alphabet[:shift]
    table = str.maketrans(alphabet, shifted_alphabet)
    return plaintext.translate(table)

print(caesar(PLACEHOLDERS['flag_32'], 13))""")
]

requirements = [
    ("Python", """(>=
    (user-score)
    10)"""),
    ("Grep", """(or
        (before "2020-05-16")
        (after "2020-05-20")
    )"""),
    ("Caesar Cipher", """(and
        (or (cohort "CS 123") (cohort "CS 456"))
        (completed 1 2))"""),
    ("Who listens in on Alice and Bob?", """(or
    (=
        (user-name)
        'alice')
    (=
        (user-name)
        'Alice')
    (=
        (user-name)
        'bob')
    (=
        (user-name)
        'Bob')
    (=
        (user-name)
        'eve')
    (=
        (user-name)
        'Eve'))""")
]

# Create challenges
with app.app_context():
    for challenge in challenges:
        if not UniqueChallenges.query.filter_by(name=challenge["name"]).first():
            row = UniqueChallenges(**challenge, category="", type="unique")
            db.session.add(row)

    for (name, content) in flags:
        challenge = UniqueChallenges.query.filter_by(name=name).one()
        if not Flags.query.filter_by(challenge_id=challenge.id, content=content).first():
            row = Flags(challenge_id=challenge.id, type='static', content=content, data='')
            db.session.add(row)

    for (c_name, name, content) in files:
        challenge = UniqueChallenges.query.filter_by(name=c_name).one()
        if not UniqueChallengeFiles.query.filter_by(challenge_id=challenge.id, name=name).first():
            row = UniqueChallengeFiles(challenge_id=challenge.id, name=name, content=bytes(content, 'utf-8'))
            db.session.add(row)

    for (c_name, name, script) in scripts:
        challenge = UniqueChallenges.query.filter_by(name=c_name).one()
        if not UniqueChallengeScript.query.filter_by(challenge_id=challenge.id, name=name).first():
            row = UniqueChallengeScript(challenge_id=challenge.id, name=name, script=bytes(script, 'utf-8'))
            db.session.add(row)

    for (name, script) in requirements:
        challenge = UniqueChallenges.query.filter_by(name=name).one()
        if not UniqueChallengeRequirements.query.filter_by(challenge_id=challenge.id).first():
            row = UniqueChallengeRequirements(challenge_id=challenge.id, script=bytes(script, 'utf-8'))
            db.session.add(row)

    db.session.commit()

users = [
    'Liam',
    'Emma',
    'Noah',
    'Olivia',
    'William',
    'Ava',
    'James',
    'Isabella',
    'Oliver',
    'Sophia',
    'Benjamin',
    'Charlotte',
    'Elijah',
    'Mia',
    'Lucas',
    'Amelia',
    'Mason',
    'Harper',
    'Logan',
    'Evelyn',
]

cohorts = [
    'CS 123',
    'CS 456',
    'CS 596'
]

# Create users
with app.app_context():
    db_users = []
    user_flags = defaultdict(list)
    db_cohorts = []

    # Create cohorts
    for name in cohorts:
        cohort = UniqueChallengeCohort.query.filter_by(name=name).first()
        if not cohort:
            cohort = UniqueChallengeCohort(name=name)
            db.session.add(cohort)
        db_cohorts.append(cohort)

    db.session.commit()

    for name in users:
        email = f'{name.lower()}@fake-email.fake'
        user = Users.query.filter_by(email=email).first()
        if not user:
            user = Users(name=name, password='password', email=email)
            user.verified = True
            db.session.add(user)
        db_users.append(user)
        # Also make unique flags
        for ch in challenges:
            challenge = UniqueChallenges.query.filter_by(name=ch['name']).one()
            flags = UniqueFlags.query.filter_by(
                challenge_id=challenge.id,
                user_id=user.id
            ).first()

            if not flags: # Missing, insert new flags
                flags = UniqueFlags(
                    challenge_id=challenge.id,
                    user_id=user.id,
                    team_id=None,
                    flag_8=token_hex(4),
                    flag_16=token_hex(8),
                    flag_32=token_hex(16)
                )
                db.session.add(flags)
            user_flags[user.id].append(flags)

        # And add users to cohorts
        rand = random.getrandbits(2)
        if rand != 3:
            if not UniqueChallengeCohortMembership.query.filter_by(user_id=user.id, cohort_id=db_cohorts[rand].id).first():
                membership = UniqueChallengeCohortMembership(user_id=user.id, cohort_id=db_cohorts[rand].id)
                db.session.add(membership)
        rand2 = random.getrandbits(2)
        if rand2 != 3 and rand2 != rand:
            if not UniqueChallengeCohortMembership.query.filter_by(user_id=user.id, cohort_id=db_cohorts[rand2].id).first():
                membership = UniqueChallengeCohortMembership(user_id=user.id, cohort_id=db_cohorts[rand2].id)
                db.session.add(membership)
    db.session.commit()

    # Create a bunch of attempts, some cheaty, some not.
    # Some successful, some not.
    Solves.query.delete()
    Submissions.query.delete()
    db.session.commit()

    for user in db_users:
        for ch in challenges:
            challenge = UniqueChallenges.query.filter_by(name=ch['name']).one()
            for _ in range(5):
                if random.getrandbits(2) == 0:
                    solve = Solves(user_id=user.id, challenge_id=challenge.id, ip="127.0.0.1", provided='correct')
                    db.session.add(solve)
                    break
                else:
                    # Failed the challenge, cheater? 25% chance.
                    if random.getrandbits(2) == 0:
                        implicit = user
                        while implicit == user:
                            implicit = random.choice(db_users)
                        for flag in user_flags[implicit.id]:
                            if flag.challenge_id == challenge.id:
                                provided = flag.flag_8
                                break
                    else:
                        provided = 'failed'
                    fail = Fails(user_id=user.id, challenge_id=challenge.id, ip="127.0.0.1", provided=provided)
                    db.session.add(fail)
    db.session.commit()

# Unique Challenges for CTFd

> This plugin was developed as part of an independent study at UCCS.

Compatible with CTFd v2.2.3

When using CTF challenges in an academic environment, it provides some benefit to give each student
a unique flag. This makes sharing answers easily detectable while still allowing students to work
together in learning the material.

When using this plugin, challenge visibility must be set to Private or Admins Only.

This plugin provides a new challenge type - unique. This challenge type lets the content author
use placeholders like `!flag_8!` to insert a dynamic value for each CTF user/team in the
challenge description or downloadable text file. It also allows administrators to write
Python 3 scripts that will be passed the placeholders to generate a downloadable text file.

## Installation

```bash
cd /path/to/CTFd/plugins
git clone git@github.com:Gerrit0/CTFd_unique_challenges.git unique_challenges
```

### Setup Script

To quickly set up a CTFd development server with this plugin installed, run the following commands

```bash
python3 -m venv env
source env/bin/activate
git clone https://github.com/CTFd/CTFd.git
cd CTFd
pip install -r requirements.txt
git clone git@github.com:Gerrit0/CTFd_unique_challenges.git CTFd/plugins/unique_challenges
python serve.py
```

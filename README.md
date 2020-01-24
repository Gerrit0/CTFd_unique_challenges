# Unique Challenges for CTFd

Compatible with CTFd v2.2.3

When using CTF challenges in an academic environment, it provides some benefit to give each student
a unique flag. This makes sharing answers easily detectable while still allowing students to work
together in learning the material.

This plugin provides two new challenge types.

1. Unique - This challenge lets the content author use placeholders like `!flag_8!` to
  insert a dynamic value for each CTF user/team in the challenge description or downloadable text file.
1. Unique Programmable - This challenge lets the content author write two generic Python 3 functions to
  generate the flag for a given user and the corresponding challenge. The 

## Installation

```bash
cd /path/to/CTFd/plugins
git clone git@github.com:Gerrit0/CTFd_unique_challenges.git unique_challenges
```


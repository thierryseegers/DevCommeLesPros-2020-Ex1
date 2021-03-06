"""Correction script for this exercise.
For each depot name found in depots.txt:
- clones the repo.
- prints the name of the repo.
- confirms test code from main.c is the same as the original.
- prints a '!' if a mismatch detected between original test code and test code in main.c.
- compiles main.c to a.out.
- runs a.out.
- prints the return code of a.out or a negative value if an earlier error occured:
    - -1: failed to clone the repo.
    - -3: failed to compile.
"""

import argparse
import datetime
import hashlib
import itertools
import os
import sys

import pygit2

ARGPARSER = argparse.ArgumentParser()
ARGPARSER.add_argument('-t', '--timestamp', dest='timestamp', action='store', metavar='TIMESTAMP(YYYY-MM-DD HH24:MM)',
                       help='Date and time at which to clone the repositories.')
ARGPARSER.add_argument('-l', '--show-log', dest='showlog', action='store_true',
                       help='Print git log of repositories.')
ARGS = ARGPARSER.parse_args()

# Verify timestamp format, if present.
if ARGS.timestamp:
    try:
        datetime.datetime.strptime(ARGS.timestamp, "%Y-%m-%d %H:%M")
    except ValueError:
        print('Bad timestamp', sys.exc_info())
        sys.exit(100)

def hash_test_code(main_path):
    """Hashes all lines in file main_path starting from 'int main()\n' until the end.
       The same function was used to hash the original main.c."""
    with open(main_path) as main:
        test_code_hash = hashlib.sha256()
        in_test_code = False
        for line in main:
            if not in_test_code and line == 'int main()\n':
                in_test_code = True
            if in_test_code:
                test_code_hash.update(line.encode())
    return test_code_hash.hexdigest()

PROFESSOR_TEST_CODE_HEXDIGEST = 'a6451d4224897bf44fb4618386fa30ce95adbc1f1ee7196cdb7e8d41dd592628'
CALLBACKS = pygit2.RemoteCallbacks(credentials=pygit2.KeypairFromAgent("git"))

with open('depots.txt') as remote_depot_names:
    for remote_depot_name in itertools.dropwhile(lambda line: line.startswith('#'),
                                                 remote_depot_names):
        try:
            # Craft URL to clone given a deopt name.
            remote_depot_name = remote_depot_name.rstrip()
            remote_depot_url = 'ssh://git@github.com/' + remote_depot_name + '.git'
            local_depot_path = remote_depot_name.replace('/', '-')
            print(local_depot_path, end='')

            # Clone the repo.
            if pygit2.clone_repository(remote_depot_url, local_depot_path, callbacks=CALLBACKS) \
                    is None:
                raise RuntimeError('-1')

            # If timestamp is specified, checkout at that point in time.
            if ARGS.timestamp:
                os.system('cd ' + local_depot_path + ' && ' +
                          'git checkout --quiet `git rev-list -n 1 --before="' + ARGS.timestamp + '" master`')

            # Confirm test code is intact.
            student_test_code_hexdigest = hash_test_code(local_depot_path + '/main.c')
            if student_test_code_hexdigest != PROFESSOR_TEST_CODE_HEXDIGEST:
                print(' !', end='')

            # Compile.
            if os.system('gcc ' + local_depot_path + '/main.c -lm -o ' + local_depot_path
                         + '/a.out') != 0:
                raise RuntimeError('-3')

            # Run and print result.
            print(' ' + str(os.WEXITSTATUS(os.system(local_depot_path + '/a.out'))))

            # If show-log is specified, show log.
            if ARGS.showlog:
                os.system('cd ' + local_depot_path + ' && git log --oneline --graph --decorate')
        except pygit2.GitError:
            print('-1')
        except RuntimeError as error:
            print(error.args[0])

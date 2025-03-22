# Import submissions downloaded from Github Classroom

import sys
import os
import argparse
import csv
from subprocess import check_output
import random
import string

from database import COMP249Db


def Parser():
  the_parser = argparse.ArgumentParser(description="ingest submissions from Github Classroom")
  the_parser.add_argument('csvfile', action="store", type=str, help="csv grade file from Github Classroom")
  the_parser.add_argument('targetdir', help="directory containing repositories")
  the_parser.add_argument('passwords', help="password CSV file")
  args = the_parser.parse_args()
  return args

def generate_password():
    """Generate a random password"""

    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))


def load_students(csvfile, targetdir, passwordCSV):
    """Load student list from github classroom csv file
    return a dictionary of {githubid: studentid}
    """

    # read any existing passwords
    passwords = dict()
    if (os.path.exists(passwordCSV)):
        with open(passwordCSV) as input:
            reader = csv.DictReader(input)
            for row in reader:
                passwords[row['email']] = row['password']

    result = dict()
    with open(csvfile) as input:
        reader = csv.DictReader(input)
        for row in reader:
            if row['roster_identifier']:
                email = row['roster_identifier']
                repodir = os.path.join(targetdir, row['student_repository_name'])
                if (os.path.exists(repodir)):
                    try:
                        cmd = check_output(["git", "log", "--oneline"], cwd=repodir).decode("utf8")
                        count = len(cmd.split('\n'))
                        if count > 0 and not email in passwords:
                            password = generate_password()
                            passwords[email] = password
                        result[email] = (email, passwords[email], repodir)
                    except: 
                        print("failed to run git in ", repodir)
                else:
                    print("No repo for ", row['roster_identifier'], repodir)
            else:
                print(row['github_username'], "has no student identifier")

    # write out generated passwords
    with open('passwords.csv', 'w') as output:
        writer = csv.writer(output)
        writer.writerow(['email', 'password'])
        for email, password in passwords.items():
            writer.writerow([email, password])

    return result


if __name__=='__main__':

    args = Parser()

    students = load_students(args.csvfile, args.targetdir, args.passwords)

    db = COMP249Db()
    db.import_users(students)


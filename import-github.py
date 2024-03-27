# Import submissions downloaded from Github Classroom

import sys
import os
import argparse
import csv
from subprocess import check_output
from tabnanny import check

from database import COMP249Db


def Parser():
  the_parser = argparse.ArgumentParser(description="ingest submissions from Github Classroom")
  the_parser.add_argument('csvfile', action="store", type=str, help="csv grade file from Github Classroom")
  the_parser.add_argument('targetdir', help="directory containing repositories")
  args = the_parser.parse_args()
  return args


def load_students(csvfile, targetdir):
    """Load student list from github classroom csv file
    return a dictionary of {githubid: studentid}
    """

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
                        if count > 2:
                            if 'password' in row:
                                password = row['password']
                            else:
                                password = row['github_username']
                            
                            result[email] = (email, password, repodir)
                        else:
                            print("No commits for", row['github_username'])
                    except: 
                        print("failed to run git in ", repodir)
                else:
                    print("No repo for ", row['roster_identifier'], repodir)
            else:
                print(row['github_username'], "has no student identifier")

    return result


if __name__=='__main__':

    args = Parser()

    students = load_students(args.csvfile, args.targetdir)

    db = COMP249Db()
    db.import_users(students)


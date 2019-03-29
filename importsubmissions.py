

from pyunitgrading import scan_or_unpack_submissions

import sys
import os
import argparse

from database import COMP249Db


def Parser():
  the_parser = argparse.ArgumentParser(description="unpack an iLearn zip file")
  the_parser.add_argument('zipfile', action="store", type=str, help="downloaded zip file")
  the_parser.add_argument('csvfile', action="store", type=str, help="downloaded csv grading file")
  the_parser.add_argument('targetdir', help="directory to store unpacked files")
  args = the_parser.parse_args()
  return args


if __name__=='__main__':

    args = Parser()

    unpacked, problems = scan_or_unpack_submissions(args.zipfile, args.targetdir, expectzip=True)

    if problems != []:
        print("PROBLEMS")
        for problem in problems:
            print(problem)

    paths = dict()
    for sid in unpacked:
        paths[sid] = os.path.abspath(os.path.join(args.targetdir, sid))

    db = COMP249Db()
    db.import_users(args.csvfile, paths)


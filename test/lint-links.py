#!/usr/bin/env python3
#
# Copyright (c) 2017-2022 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
#
# Check for new lines in diff that introduce PR-specific links that may break in the future.


import argparse
import os
import re
import sys

from subprocess import check_output

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="""
            Check for new lines in diff that introduce links that may break in the future,
            previous n commits, or a commit-range.
        """,
        epilog=f"""
            You can manually set the commit-range with the COMMIT_RANGE
            environment variable (e.g. "COMMIT_RANGE='47ba2c3...ee50c9e'
            {sys.argv[0]}"). Defaults to current merge base when neither
            prev-commits nor the environment variable is set.
        """)

    parser.add_argument("--prev-commits", "-p", required=False, help="The previous n commits to check")

    return parser.parse_args()


def get_diff(commit_range):
    what_files = ["*.md"]

    diff = check_output(["git", "diff", "-U0", commit_range, "--"] + what_files, universal_newlines=True, encoding="utf8")

    return diff

def contains_pull_specific_link(line):
    # Link to a commit in a PR
    if re.match(r".*github\.com/bitcoin/bitcoin/pull/\d+/commits/.*", line):
        return True
    # Link to a diff in a PR
    if re.match(r".*github\.com/bitcoin/bitcoin/pull/\d+/\#diff.*", line):
        return True
    return False

def main():
    args = parse_args()

    if not os.getenv("COMMIT_RANGE"):
        if args.prev_commits:
            commit_range = "HEAD~" + args.prev_commits + "...HEAD"
        else:
            # This assumes that the target branch of the pull request will be master.
            merge_base = check_output(["git", "merge-base", "HEAD", "master"], universal_newlines=True, encoding="utf8").rstrip("\n")
            commit_range = merge_base + "..HEAD"
    else:
        commit_range = os.getenv("COMMIT_RANGE")

    pull_specific_links = []
    for line in get_diff(commit_range).splitlines():
        if contains_pull_specific_link(line):
            pull_specific_links.append(line)

    ret = 0

    if len(pull_specific_links) > 0:
        print("This diff appears to have added a link to a PR-specific diff or line of code.")
        print("This link will break if the pull request changes in the future.")
        print("Please push a tag to the review club website repository and link there instead (see hosting.md for help).")
        for line in pull_specific_links:
            # This would be more helpful if it printed the filename and line number, but almost all
            # PRs consist of 1 commit changing 1 file, so it should be fine for now.
            print(line)
        ret = 1
    else:
        print("Success!")

    sys.exit(ret)


if __name__ == "__main__":
    main()

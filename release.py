#!/usr/bin/env python3
#
# Release script for playactor
#

import os
import datetime
from collections import OrderedDict

try:
    from hostage import *  # pylint: disable=unused-wildcard-import,wildcard-import
except ImportError:
    print("!! Release library unavailable.")
    print("!! Use `pip install hostage` to fix.")
    print("!! A $GITHUB_TOKEN env variable is needed.")
    exit(1)

# Set GitHub Token and Repository from Environment Variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY')

if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
    print("!! Environment variables GITHUB_TOKEN and GITHUB_REPOSITORY must be set.")
    exit(1)

# Initialize GitHub with Token
github = Github(GITHUB_TOKEN)

# Define Global Variables
notes = File(".last-release-notes")
latestTag = git.Tag.latest(branch='main')

# Function Definitions
def formatIssue(issue):
    return "- {title} (#{number})\n".format(number=issue.number, title=issue.title)

def buildLabeled(labelsToTitles):
    result = OrderedDict()
    for k, v in labelsToTitles:
        result[k] = {'title': v, 'content': ''}
    return result

def buildDefaultNotes(_):
    if not latestTag:
        return "Initial release."
    
    logParams = {
        'path': latestTag.name + "..HEAD",
        'grep': ["Fix #", "Fixes #", "Closes #"],
        'pretty': "format:- %s"
    }
    logParams["invertGrep"] = True
    msgs = git.Log(**logParams).output()

    contents = ''
    lastReleaseDate = latestTag.get_created_date() if latestTag else datetime.datetime.now()
    closedIssues = github.get_repo(GITHUB_REPOSITORY).get_issues(state='closed', since=lastReleaseDate)

    labeled = buildLabeled([
        ('feature', "New Features"),
        ('enhancement', "Enhancements"),
        ('bug', "Bug Fixes"),
        ('_default', "Other resolved tickets"),
    ])

    for issue in closedIssues:
        found = False
        for label in issue.labels:
            if label.name in labeled:
                labeled[label.name]['content'] += formatIssue(issue)
                found = True
                break
        if not found:
            labeled['_default']['content'] += formatIssue(issue)

    for label, data in labeled.items():
        if data['content']:
            contents += "\n**{}**:\n{}".format(data['title'], data['content'])

    if msgs:
        contents += "\n**Notes**:\n" + msgs
    return contents.strip()

# Script Execution Flow
if __name__ == "__main__":
    version = verify(File("package.json").filtersTo(RegexFilter('"version": "(.*)"'))).valueElse(None)
    if not version:
        print("No version found in package.json.")
        exit(1)

    versionTag = "v" + version  # Assuming version prefix
    releaseNotes = buildDefaultNotes(None)

    # Example of publishing release (simplified, implement as needed)
    repo = github.get_repo(GITHUB_REPOSITORY)
    repo.create_git_release(tag=versionTag, name="Release " + versionTag, message=releaseNotes, draft=False, prerelease=False)

    print("Release {} created successfully.".format(versionTag))

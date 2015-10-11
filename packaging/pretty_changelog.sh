#!/bin/bash
#
# Print a pretty changelog suitable for posting to a homepage or release post
# based on the release commit messages that usually contain a nice human
# readable summary of changes in the given release.

git log --format="%s (%ad)%n%n%b" --grep="New modRana version" --date=short | sed "s/^New modRana version/modRana/g"

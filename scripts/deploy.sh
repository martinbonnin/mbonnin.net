#!/usr/bin/env bash 

rsync -e ssh -avz --progress --delete-after site/ root@ovh.mbonnin.net:

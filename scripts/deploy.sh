#!/usr/bin/env bash 

rsync -e 'ssh -p 27095' -avz --progress --delete-after site/ root@ovh.mbonnin.net:site

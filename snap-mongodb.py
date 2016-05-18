#!/usr/bin/env python
# Version: 1.0
#
# version 1.0: Forked aws-snapshot-tool at version 3.3

import requests
import argparse

from datetime import datetime
import time
import sys
import logging

from pymongo import MongoClient
import boto3
#from config import config

def check_if_primary(config):
    mongo_uri = "mongodb://%(username)s:%(password)s@localhost/admin" % { username: config.user, password: config.password }
    logging.debug("Connecting to MonogoDB: %s" % mongo_uri)
    client = MongoClient(mongo_uri)
    try:
        return client.is_primary
    except:
        return False

def get_instance():
    """
    Query cloud-init for aws instance ID
    """
    logging.debug("Querying cloud-init for instance-id")
    instance_id = requests.get("http://169.254.169.254/latest/meta-data/instance-id").text
    client = boto3.client('ec2')
    return client.describe_instances(InstanceIds=[instance_id])

def curdate():
        return datetime.today().strftime('%d-%m-%Y %H:%M:%S')

get get_instance

def main():
    """
    Create Snapshots of attached mongodb volumes - based on EC2 EBS Tag
    """
    parser = argparse.ArgumentParser(description='Snapshot MongoDB EBS RAID disks')
    parser.add_argument('-u', dest="user", help="Local MongoDB user")
    parser.add_argument('-p', dest="password", help="Local MongoDB password")
    parser.add_argument('--primary', action='store_true', dest="is_primary", default=False, help="Take Snapshot even in MongoDB is Primary")
    parser.add_argument('--loglevel', action="store", dest="loglevel", default='INFO', help="Log Level")
    config = parser.parse_args()
    loglevel = getattr(logging, config.loglevel.upper())
    logging.basicConfig(filename='/var/log/snapshot-mongodb.log', level=loglevel )
    # TODO: Better way to do this... likely...
    if check_if_primary(config) and not config.is_primary:
        logging.info("%s - Local MongoDB is current Primary - Not running snapshot" % curdate())
        sys.exit(0)
    logging.info("%s - Starting MongoDB disk snapshots" % curdate())
    # Get my instance ID
    instance = get_instance()
    logging.debug("%(date)s - Instance %(instance_id)s" % {
                        "date": curdate(),
                        "instance_id": instance['Reservations'][0]['Instances'][0]['InstanceId']
                        } )


if __name__ == '__main__':
    main()

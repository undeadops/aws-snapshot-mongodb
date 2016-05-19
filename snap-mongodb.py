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

import pprint

from pymongo import MongoClient
import boto3
#from config import config

def mongo_lock(config):
    mongo_uri = "mongodb://%(username)s:%(password)s@localhost/admion" % {"username": config.username, "password": config.password }
    logging.info("Locking MongoDB")
    client = MongoClient(mongo_uri)
    try:
        return client.fsync(lock=True)
    except:
        return False


def mongo_unlock(config):
    mongo_uri = "mongodb://%(username)s:%(password)s@localhost/admion" % {"username": config.username, "password": config.password }
    logging.info("UnLocking MongoDB")
    client = MongoClient(mongo_uri)
    try:
        return client.unlock()
    except:
        return False


def mongo_check_if_primary(config):
    mongo_uri = "mongodb://%(username)s:%(password)s@localhost/admin" % { "username": config.username, "password": config.password }
    logging.debug("Connecting to MonogoDB: %s" % mongo_uri)
    client = MongoClient(mongo_uri)
    try:
        return client.is_primary
    except:
        return False


def create_snapshot(volumes):
    """
    Create Snapshots from List volumes
    """
    ec2 = boto3.resource("ec2")
    snapshots = []
    for volume in volumes:
        for tag in volume['volume_tags']:
            if tag['Key'] == 'Name':
                volume_name = tag['Value']
        description = "Snapshot of %s - Created %s" % ( volume_name, curdate() )
        snapshot = ec2.create_snapshot(VolumeId=volume['VolumeId'], Description=description)
        logging.info("%s - Creating Snapshot of %s - SnapshotId: %s" % (curdate(), snapshot.volume_id, snapshot.id))
        snapshots.append(snapshot)
        tags = snapshot.create_tags(
                Tags=volume['volume_tags']
        )
        logging.info("%s Updated Tags on Snapshot: %s" % (curdate, snapshot.id))
    return snapshots


def get_volumes(instance):
    """
    With Instance, take Instance Name append _data, return list of matching volume ids
    """
    volumes = []
    for tag in instance['Tags']:
        if tag['Key'] == 'Name':
            volume_tag_reference = "%s_data" % tag['Value']

    for volume in instance['volumes']:
        if volume['volume_tags'] != None:
            for volume_tag in volume['volume_tags']:
                if volume_tag['Key'] == 'Name' and volume_tag['Value'] == volume_tag_reference:
                    volumes.append(volume['VolumeId'])
    snapshot_volumes = []
    for volume in instance['volumes']:
        if volume['VolumeId'] in volumes:
            vol = {"VolumeId": volume['VolumeId'], "volume_tags": volume['volume_tags']}
            snapshot_volumes.append(vol)
    return snapshot_volumes


def get_instance():
    """
    Query cloud-init for aws instance ID
    """
    logging.debug("Querying cloud-init for instance-id")
    instance_id = requests.get("http://169.254.169.254/latest/meta-data/instance-id").text
    client = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')
    aws_instance = client.describe_instances(InstanceIds=[instance_id])
    instance = aws_instance['Reservations'][0]['Instances'][0]
    ebs_volumes = []
    for device in instance['BlockDeviceMappings']:
        volume_info = ec2_resource.Volume(device['Ebs']['VolumeId'])
        ebs_volume = {u"VolumeId": device['Ebs']['VolumeId'],
                      u"DeviceName": device['DeviceName'],
                      u"volume_type": volume_info.volume_type,
                      u"size": volume_info.size,
                      u"snapshot_id": volume_info.snapshot_id,
                      u"iops": volume_info.iops,
                      u"availability_zone": volume_info.availability_zone,
                      u"encrypted": volume_info.encrypted,
                      u"volume_tags": volume_info.tags }
        ebs_volumes.append(ebs_volume)
    instance[u'volumes'] = ebs_volumes
    return instance


def curdate():
        return datetime.today().strftime('%m-%d-%Y %H:%M:%S')


def main():
    """
    Create Snapshots of attached mongodb volumes - based on EC2 EBS Tag
    """
    parser = argparse.ArgumentParser(description='Snapshot MongoDB EBS RAID disks')
    parser.add_argument('-u', dest="username", help="Local MongoDB user")
    parser.add_argument('-p', dest="password", help="Local MongoDB password")
    parser.add_argument('--primary', action='store_true', dest="is_primary", default=False, help="Take Snapshot even in MongoDB is Primary")
    parser.add_argument('--loglevel', action="store", dest="loglevel", default='INFO', help="Log Level")
    config = parser.parse_args()
    loglevel = getattr(logging, config.loglevel.upper())
    logging.basicConfig(filename='/var/log/snapshot-mongodb.log', level=loglevel )
    logging.getLogger('boto').setLevel(logging.CRITICAL)
    # TODO: Better way to do this... likely...
    if mongo_check_if_primary(config) and not config.is_primary:
        logging.info("%s - Local MongoDB is current Primary - Not running snapshot" % curdate())
        sys.exit(0)
    logging.info("%s - Starting MongoDB disk snapshots" % curdate())
    # Get my instance ID
    instance = get_instance()
    logging.debug("%(date)s - Instance %(instance_id)s" % {
                        "date": curdate(),
                        "instance_id": instance['InstanceId']
                        } )

    # Get volumes labeld <hostname>_data - Used for Mongo
    volumes = get_volumes(instance)
    logging.info("%s - Backing up volume Ids: %s" % (curdate(), volumes))
    # Run Lock and Snapshot
    mongo_lock(config)
    snapshots = create_snapshot(volumes)
    logging.debug("Snapshots Created: %s " % snapshots)
    mongo_unlock(config)


if __name__ == '__main__':
    main()

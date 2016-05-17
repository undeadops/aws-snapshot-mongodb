aws-snapshot-mongodb
=================
aws-snapshot-mongodb is a python script to make it easy to *roll snapshot of your EBS volumes*.

This script is a modification of work done by (evannuil/aws-snapshot-tool)[https://github.com/evannuil/aws-snapshot-tool]

To make it work better with mongodb specifically.  

Simply add a tag to each volume you want snapshots of, configure and install a cronjob for aws-snapshot-mongodb and you are off.

Features:
- *Python based*: Leverages boto and is easy to configure and install as a crontab
- *SNS Notifications*: aws-snapshot-tool works with Amazon SNS our of the box, so you can be notified of snapshots

Usage (Needs to be rewritten...)
==========
1. Install and configure Python and Boto (See: https://github.com/boto/boto)
2. Clone Repo `cd /opt && git clone https://github.com/undeadops/aws-snapshot-mongodb`
2. Create a SNS topic in AWS and copy the ARN into the config file
3. Subscribe with a email address to the SNS topic
4. Create a snapshot user in IAM and put the key and secret in the config file
5. Create a security policy for this user (see the iam.policy.sample)
6. Copy config.sample to config.py
7. Decide how many versions of the snapshots you want for day/week/month and change this in config.py
8. Change the Region and Endpoint for AWS in the config.py file
9. Optionally specify a proxy if you need to, otherwise set it to '' in the config.py
10. Give every Volume for which you want snapshots a Tag with a Key and a Value and put these in the config file. Default: "MakeSnapshot" and the value "True"
11. Install the script in the cron: 

		# chmod +x snap-mongodb.py
		30 3 1 * * /opt/aws-snapshot-mongodb/snap-mongodb.py

Additional Notes
=========
The user that executes the script needs the following policies: see iam.policy.sample

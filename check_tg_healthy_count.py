#!/usr/bin/env python3
# encoding: utf-8

import os, sys, configparser, boto, smtplib
from optparse import OptionParser
import boto3
from botocore.exceptions import ClientError

USAGE = """\nUsage: check_alb_health.py -t <target group name> [-w <warning threshold>] -c <critical threshold> [-r <aws region>]"""
config = configparser.ConfigParser()

def validate_thresholds(warn, crit):
	# Verify thresholds are numeric
	for i in ('-w (--warning)', warn), ('-c (--critical)', crit):
		try: 
			int(i[1])
		except ValueError:
			print('Error: "{}" is not numeric.  Argument "{}" expects a number.'.format(i[1], i[0]))
			sys.exit(3)
	
	if int(warn) < int(crit):
		print('Error: Warning threshold {} less than critical threshold {}.'.format(warn, crit))
		print(USAGE)
		sys.exit(3)

def main():
	# Parse arguments
	parser = OptionParser()
	parser.add_option("-t", "--targetgroup", dest="tg", help="Amazon Target Group name")
	parser.add_option("-w", "--warning", dest="warn", help="warning threshold")
	parser.add_option("-c", "--critical", dest="crit", help="critical threshold")
	parser.add_option("-r", "--region", dest="region", help="aws region")
	(options, args) = parser.parse_args()
	tg = options.tg
	warn = options.warn
	crit = options.crit
	region = options.region

	
	if not crit:
		print("Error: No critical threshold specified.")
		print(USAGE)
		sys.exit(3)
	
	if not warn:
		warn = crit
	
	# Perform sanity checks on thresholds
	validate_thresholds(warn, crit)
	
	if not tg:
		print("Error: No queue specified.")
		print(USAGE)
		sys.exit(3)
	if not region:
		print("Warning, No region specified, defaulting to us-east-1")
		aws_region = "us-east-1"
	healthy_count = 0
	
	try:
		client = boto3.client('elbv2',region)
		tg_list = client.describe_target_groups()
		target_group_arn = ""
		for target_group in tg_list['TargetGroups']:
			if target_group['TargetGroupName'] == tg:
				target_group_arn = target_group['TargetGroupArn']

		if target_group_arn == "":
			print("Could not find specified target group: {}".format(tg))
			sys.exit(3)
		else:
			targets = client.describe_target_health(TargetGroupArn=target_group_arn)
			for target in targets['TargetHealthDescriptions']:
				if target['TargetHealth']['State'] == "healthy":
					healthy_count = healthy_count+1

	except ClientError as err:
		print("Aws Error: {}".format(err))
		sys.exit(3)

    # Get queue length, compare to thresholds, and take appropriate action
	

	if int(healthy_count) > int(warn):
		print('Target Group OK: "{}" contains {} healthy targets.'.format(tg, healthy_count))
		sys.exit(0)
	elif int(healthy_count) <= int(crit):
		print('Target Group CRITICAL: "{}" contains {} healthy targets.'.format(tg, healthy_count))
		sys.exit(2)
	else:
		print('Target Group WARNING: "{}" contains {} healthy targets.'.format(tg, healthy_count))
		sys.exit(1)
	
if __name__ == '__main__':
	main()

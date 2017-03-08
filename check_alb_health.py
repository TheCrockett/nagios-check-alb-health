#!/usr/bin/env python3
# encoding: utf-8

import os, sys, configparser, boto, smtplib
from optparse import OptionParser
import boto3
from botocore.exceptions import ClientError

USAGE = """\nUsage: check_alb_health.py -a <alb name> [-w <warning threshold>] -c <critical threshold> [-r <aws region>]"""
config = configparser.ConfigParser()

def validate_thresholds(warn, crit):
	# Verify thresholds are numeric
	for i in ('-w (--warning)', warn), ('-c (--critical)', crit):
		try: 
			int(i[1])
		except ValueError:
			print('Error: "{}" is not numeric.  Argument "{}" expects a number.'.format(i[1], i[0]))
			sys.exit(3)
	
	if int(warn) > int(crit):
		print('Error: Warning threshold {} exceeds critical threshold {}.'.format(warn, crit))
		print(USAGE)
		sys.exit(3)

def main():
	# Parse arguments
	parser = OptionParser()
	parser.add_option("-a", "--alb", dest="alb", help="Amazon ALB name")
	parser.add_option("-w", "--warning", dest="warn", help="warning threshold")
	parser.add_option("-c", "--critical", dest="crit", help="critical threshold")
	parser.add_option("-r", "--region", dest="region", help="aws region")
	(options, args) = parser.parse_args()
	alb = options.alb
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
	
	if not alb:
		print("Error: No queue specified.")
		print(USAGE)
		sys.exit(3)
	if not region:
		print("Warning, No region specified, defaulting to us-east-1")
		aws_region = "us-east-1"
	unhealthy_count = 0
	
	try:
		client = boto3.client('elbv2',region)
		lb_list = client.describe_load_balancers(Names=[alb])
		
		for lb in lb_list['LoadBalancers']:
			tg_list = client.describe_target_groups(LoadBalancerArn=lb['LoadBalancerArn'])
			for tg in tg_list['TargetGroups']:
				targets = client.describe_target_health(TargetGroupArn=tg['TargetGroupArn'])
				for target in targets['TargetHealthDescriptions']:
					if target['TargetHealth']['State'] != "healthy":
						unhealthy_count = unhealthy_count+1
	except ClientError as err:
		print("Aws Error: {}".format(err))
		sys.exit(3)

    # Get queue length, compare to thresholds, and take appropriate action
	

	if int(unhealthy_count) < int(warn):
		print('ALB OK: "{}" contains {} unhealthy targets.'.format(alb, unhealthy_count))
		sys.exit(0)
	elif int(unhealthy_count) >= int(crit):
		print('Alb CRITICAL: "{}" contains {} unhealthy targets.'.format(alb, unhealthy_count))
		sys.exit(2)
	else:
		print('ALB WARNING: "{}" contains {} unhealthy targets.'.format(alb, unhealthy_count))
		sys.exit(1)
	
if __name__ == '__main__':
	main()

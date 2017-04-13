## AWS ALB Nagios Checks

The check_alb_health.py script will scan an ELBv2 (Application load Balancer) for its target groups, and then scan each of those target groups to ensure each instance is healthy. 
Usage: check_alb_health.py -a <asg_name> -w <warn_level> -c <crit_level> -r <aws_region>

The check_tg_healthy_count.py script will check a target group for a minimum number of healthy targets (hosts). 
Usage: check_tg_healthy_count.py -t <target_group_name> -w <warn_level> -c <crit_level> -r <aws_region>

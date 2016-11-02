import boto3
import time

def lambda_handler(event, context):
    contextVariables = context.invoked_function_arn
    contextVariables = contextVariables.split(":")
    region = contextVariables[3]
    accountId = contextVariables[4]
    ddsnsArn="arn:aws:sns:"+region+":"+accountId+":ebs-snapshot-to-datadog"

    amiId  = event['ami-id']
    launchConfigName = event['launch-config-name']
    ec2 = boto3.resource('ec2', region_name=region)
    asg = boto3.client('autoscaling', region_name=region)
    
    snapshot = ec2.Snapshot(snapshotId)
    tags = snapshot.tags
    keyValues = {}
    for tag in tags:
        keyValues[tag['Key']] = tag['Value']
    
    asgResp = asg.create_launch_configuration(
        LaunchConfigurationName=launchConfigName+time.strftime("%Y-%m-%d-%H-%M-%S"),
        ImageId=amiId,
        KeyName=keyValues['KeyName'],
        SecurityGroups=keyValues['SecurityGroups'],
        BlockDeviceMappings=[{"DeviceName":keyValues['RootDeviceName'],
        "Ebs":{"VolumeSize":int(keyValue['VolumeSize']),
        "DeleteOnTermination":True,
        "VolumeType":keyValue['VolumeType']}}], 
        EbsOptimized=True, 
        IamInstanceProfile=keyValue['IamInstanceProfile'],
        InstanceMonitoring={"Enabled":True},
        InstanceType=keyValue['InstanceType'],
        AssociatePublicIpAddress=True)
    
    return asgResp
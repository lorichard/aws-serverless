import boto3
import time

def lambda_handler(event, context):
    contextVariables = context.invoked_function_arn
    contextVariables = contextVariables.split(":")
    region = contextVariables[3]
    accountId = contextVariables[4]
    ddsnsArn="arn:aws:sns:"+region+":"+accountId+":ebs-snapshot-to-datadog"
    snsArn="arn:aws:sns:"+region+":"+accountId+":ebs-snapshot-"+region
    
    snapshotId  = event['snapshot-id']
    amiName = event['ami-name']
    ec2 = boto3.resource('ec2', region_name=region)
    asg = boto3.client('autoscaling', region_name=region)
    
    snapshot = ec2.Snapshot(snapshotId)
    tags = snapshot.tags
    keyValues = {}
    for tag in tags:
        keyValues[tag['Key']] = tag['Value']
    
    
    ec2Resp= ec2.register_image(
        Name=amiName+time.strftime("-%Y-%m-%d-%H-%M-%S"),
        Description=amiName+"-ami",
        Architecture=keyValues['Architecture'],
        RootDeviceName=keyValues['RootDeviceName'],
        VirtualizationType=keyValues['VirtualizationType'],
        BlockDeviceMappings=[{
            'DeviceName':keyValues['RootDeviceName'], 
            'Ebs':{'VolumeType':keyValues['VolumeType'],
            'VolumeSize':int(keyValues['VolumeSize']),
            'SnapshotId':snapshotId}}])
    
    return "The AMI "+ ec2Resp.id + " was created at : " + ec2Resp.creation_date
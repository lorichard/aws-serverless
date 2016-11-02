import json
import boto3
import datetime
import collections
import copy


def do_tagging(ec2, snapshotID, deleteOn, instanceID, instanceName, volumeID, volumeType, VPCID, subnetID, instanceType,architecture,virtualizationType,rootDeviceName,keyName,securityGroups,volumeSize,iamInstanceProfile):
    snapshot = ec2.Snapshot(snapshotID)
    securityGroups = json.dumps(securityGroups)
    snapshot.create_tags(
            Tags=[
                {'Key': 'DeleteOn', 'Value': deleteOn},
                {'Key': 'InstanceID', 'Value': instanceID},
                {'Key': 'InstanceName', 'Value': instanceName},
                {'Key': 'VolumeID', 'Value': volumeID},
                {'Key': 'VolumeType', 'Value': volumeType},
                {'Key': 'VPCID', 'Value': VPCID},
                {'Key': 'SubnetID', 'Value': subnetID},
                {'Key': 'InstanceType', 'Value': instanceType},
                {'Key': 'Architecture', 'Value': architecture},
                {'Key': 'VirtualizationType', 'Value': virtualizationType},
                {'Key': 'RootDeviceName', 'Value': rootDeviceName},
                {'Key': 'KeyName', 'Value': keyName},
                {'Key': 'SecurityGroups', 'Value': securityGroups},
                {'Key': 'VolumeSize', 'Value': str(volumeSize)},
                {'Key': 'IamInstanceProfile', 'Value': iamInstanceProfile}
            ]
        )

def lambda_handler(event, context):
    contextVariables = context.invoked_function_arn
    contextVariables = contextVariables.split(":")
    region = contextVariables[3]
    accountId = contextVariables[4]
    ddsnsArn="arn:aws:sns:"+region+":"+accountId+":ebs-snapshot-to-datadog"
    snsArn="arn:aws:sns:"+region+":"+accountId+":ebs-snapshot-"+region

    ec2 = boto3.resource('ec2', region_name=region)
    sns = boto3.client('sns')
    today = unicode(datetime.date.today())

    message = event['Records'][0]['Sns']['Message']
    parsed_message = json.loads(message , strict=False)

    snapshotID = parsed_message['lambda']['SnapshotID']
    deleteOn = parsed_message['lambda']['DeleteOn']
    instanceID = parsed_message['lambda']['InstanceID']
    instanceName = parsed_message['lambda']['InstanceName']
    volumeID = parsed_message['lambda']['VolumeID']
    volumeType = parsed_message['lambda']['VolumeType']
    VPCID = parsed_message['lambda']['VPCID']
    subnetID = parsed_message['lambda']['SubnetID']
    instanceType = parsed_message['lambda']['InstanceType']
    architecture = parsed_message['lambda']['Architecture']
    virtualizationType = parsed_message['lambda']['VirtualizationType']
    rootDeviceName = parsed_message['lambda']['RootDeviceName']
    keyName = parsed_message['lambda']['KeyName']
    securityGroups = parsed_message['lambda']['SecurityGroups']
    volumeSize = parsed_message['lambda']['VolumeSize']
    iamInstanceProfile = parsed_message['lambda']['IamInstanceProfile']

    print("From SNS: " + message)
    print("SnapshotID: " + snapshotID)
    print("DeleteOn: " + deleteOn)
    print("InstanceID: " + instanceID)
    print("InstanceName: " + instanceName)
    print("VolumeID: " + volumeID)
    print("VolumeType: " + volumeType)
    print("VPCID: " + VPCID)
    print("SubnetID: " + subnetID)
    print("InstanceType: " + instanceType)
    print("Architecture: " + architecture)
    print("VirtualizationType: " + virtualizationType)
    print("RootDeviceName: " + rootDeviceName)
    print("KeyName: " + keyName)
    print("SecurityGroups: " + str(securityGroups))
    print("VolumeSize: " + str(volumeSize))
    print("IamInstanceProfile: " + iamInstanceProfile)
    

    do_tagging(ec2,snapshotID,deleteOn,instanceID, instanceName, volumeID,volumeType,VPCID,subnetID,instanceType,architecture,virtualizationType,rootDeviceName,keyName,securityGroups,volumeSize,iamInstanceProfile)

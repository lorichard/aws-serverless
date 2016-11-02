import json
import boto3
import datetime
import collections
import copy

toTag = collections.defaultdict(list)
retentionDays = 30

def do_tagging(ec2, snap, instance, volume, retentionDays,taggingsnsARN):
    delete_date = datetime.date.today() + datetime.timedelta(days=retentionDays)
    delete_fmt = delete_date.strftime('%Y-%m-%d')
    print "Will delete %d snapshots on %s" % (len(toTag[retentionDays]), delete_fmt)
    tags = instance.tags
    for tag in tags:
        if tag['Key'] == "Name":
            instanceName = tag['Value']

    sg = instance.security_groups
    securityGroups=[]
    for group in sg:
        securityGroups.append(group['GroupId'])
    
    #if an IAM Instance Profile is defined    
    try:
        json_msg=json.dumps({"lambda": 
            {"SnapshotID": snap.snapshot_id, 
            "DeleteOn": delete_fmt,
            "InstanceID": instance.instance_id, 
            "InstanceName": instanceName, 
            "VolumeID": volume.volume_id, 
            "VolumeType": volume.volume_type, 
            "VPCID": instance.vpc_id, 
            "SubnetID": instance.subnet_id, 
            "InstanceType": instance.instance_type, 
            "Architecture": instance.architecture, 
            "VirtualizationType": instance.virtualization_type, 
            "RootDeviceName": instance.root_device_name, 
            "KeyName": instance.key_name, 
            "SecurityGroups": securityGroups, 
            "VolumeSize": snap.volume_size, 
            "IamInstanceProfile": instance.iam_instance_profile['Arn']}})
    #otherwise set the IAM Instance Profile as None
    except:
        json_msg=json.dumps({"lambda": 
            {"SnapshotID": snap.snapshot_id, 
            "DeleteOn": delete_fmt,
            "InstanceID": instance.instance_id, 
            "InstanceName": instanceName, 
            "VolumeID": volume.volume_id, 
            "VolumeType": volume.volume_type, 
            "VPCID": instance.vpc_id, 
            "SubnetID": instance.subnet_id, 
            "InstanceType": instance.instance_type, 
            "Architecture": instance.architecture, 
            "VirtualizationType": instance.virtualization_type, 
            "RootDeviceName": instance.root_device_name, 
            "KeyName": instance.key_name, 
            "SecurityGroups": securityGroups, 
            "VolumeSize": snap.volume_size, 
            "IamInstanceProfile": "None"}})
        
    sns = boto3.client('sns')
    sns.publish(TopicArn=taggingsnsARN,Message=json_msg)

def do_snapshot(ec2,instance, volume, time, desc,taggingsnsARN):
    snap =volume.create_snapshot(Description=desc + instance.id + ", volume id: " + volume.volume_id +" taken on " + time )
    toTag[retentionDays].append(snap.id)
    do_tagging(ec2, snap, instance, volume, retentionDays,taggingsnsARN)

    return snap

def lambda_handler(event, context):
    contextVariables = context.invoked_function_arn
    contextVariables = contextVariables.split(":")
    region = contextVariables[3]
    accountId = contextVariables[4]
    ddsnsArn="arn:aws:sns:"+region+":"+accountId+":ebs-snapshot-to-datadog"
    snsArn="arn:aws:sns:"+region+":"+accountId+":ebs-snapshot-"+region
    taggingsnsARN="arn:aws:sns:"+region+":"+accountId+":ebs-snapshot-tagging-"+region

    ec2 = boto3.resource('ec2', region_name=region)
    sqs = boto3.resource('sqs')
    sns = boto3.client('sns')
    today = unicode(datetime.date.today())
    desc = "EBS Snapshot of the instance: "

    queueName = 'ebs-snapshots-'+region
    queue = sqs.get_queue_by_name(QueueName=queueName)

    try:
        instances=[]
        #needs to be updated to 
        while True:
            messages = queue.receive_messages()
            #if queue is no longer returning messages, break out
            if bool(messages) == False:
                break
            for m in messages:
                instances.append(m.body)
                m.delete()

        numberInstances = len(instances)
        leftoverInstances = copy.deepcopy(instances)
        print instances
        print "There are : " + str(numberInstances) + " snapshots to be created"

        for i in instances:
            instance = ec2.Instance(i)
            volumes_iterator = instance.volumes
            volumes = list(volumes_iterator.all())

            #snapshot each volume
            for v in volumes:
                if (context.get_remaining_time_in_millis() >= 5000):
                    snap = do_snapshot(ec2,instance,v,today,desc,taggingsnsARN)
                    print "snapshot has been created for instance: " + instance.id + " of the volume: " + v.volume_id
                else:
                    raise ValueError("The Lambda function has timed-out")

            leftoverInstances.remove(i)

        print leftoverInstances
        if len(leftoverInstances) == 0:
            print "There is nothing leftover to snapshot"
            snsData = {}
            snsData['status'] = "success"
            snsData['time'] = str(datetime.datetime.now())
            snsData['msg'] = "ebs-snapshot-queue-handler - " + str(numberInstances) + " snapshots were created."
            snsData['region'] = region
            snsData['instances'] = instances

            #publish a SNS message that will notify datadog of the success
            response = sns.publish(
                TargetArn=ddsnsArn,
                Message=json.dumps(snsData))

    except Exception as e:
        print(e)
        print("There are leftover snapshots: ")
        print leftoverInstances
        print "Sending leftover instances to SQS"
        for i in leftoverInstances:
            queue.send_message(MessageBody=i)
        snsData = {}
        snsData['status']="failure"
        snsData['time'] = str(datetime.datetime.now())
        snsData['msg']="There are " + str(len(leftoverInstances)) + " instances left to be snapshotted"
        snsData['region']= region
        snsData['instances'] = leftoverInstances
        #publish a SNS message that will notify datadog of the failure
        ddresponse = sns.publish(
            TargetArn=ddsnsArn,
            Message=json.dumps(snsData))
        #publish a SNS message that will trigger the ebs-snapshot-queue function
        response = sns.publish(
            TargetArn=snsArn,
            Message=json.dumps(snsData))
        return snsData

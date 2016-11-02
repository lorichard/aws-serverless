import json
import boto3
import datetime
import collections

def lambda_handler(event, context):
    contextVariables = context.invoked_function_arn
    contextVariables = contextVariables.split(":")
    region = contextVariables[3]
    accountId = contextVariables[4]
    ddsnsArn="arn:aws:sns:"+region+":"+accountId+":ebs-snapshot-to-datadog"
    snsArn="arn:aws:sns:"+region+":"+accountId+":ebs-snapshot-"+region

    ec2 = boto3.resource('ec2', region_name=region)
    sqs = boto3.resource('sqs')
    sns = boto3.client('sns')
    queueName = 'ebs-snapshots-'+region
    queue = sqs.get_queue_by_name(QueueName=queueName)

    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    runningInstances = []

    listToIgnore = []
    for i in instances:
        tags = i.tags
        for tag in tags:
            if (tag['Key'] == "Project" and tag['Value'] == "mdn-trial") or (tag['Key'] == "Project" and tag['Value'] == "trial") :
                listToIgnore.append(i.instance_id)

        if i.state['Name'] == "running" and i.instance_id not in listToIgnore:
            runningInstances.append(i.instance_id)
            #add instances to SQS
            queue.send_message(MessageBody=i.instance_id)
            print i.id

    #Generate the message
    snsData = {}
    snsData['time'] = str(datetime.datetime.now())
    snsData['msg'] = "ebs-snapshot-scheduler - There are " + str(len(runningInstances)) + " instances that need to be snapshotted."
    snsData['instances'] = runningInstances

    #publish a SNS message that will trigger the ebs-snapshot-queue function
    response = sns.publish(
        TargetArn=ddsnsArn,
        Message=json.dumps(snsData))

    #publish a SNS message that will notify datadog of the impending snapshots
    ddresponse = sns.publish(
        TargetArn=snsArn,
        Message=json.dumps(snsData))

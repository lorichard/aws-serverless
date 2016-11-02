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
    
    try:
        print "this request is coming from the API Gateway"
        instanceId = event['body-json']['instance-id']
    except:
        print "otherwise, this request is being invoked by SNS"
        instanceId = event['instance-id']

        
    instances = ec2.instances.filter(
        Filters=[{'Name':'instance-id', 'Values':[instanceId]}])
    
    print instances
    

    runningInstances = []
    
    for i in instances:
        runningInstances.append(i.instance_id)
        queue.send_message(MessageBody=i.instance_id)
        print i.instance_id
    
    if (len(runningInstances) == 0):
        return "Error: There were no running instances with the instance-id : "+ instanceId
        

    #Generate the message
    snsData = {}
    snsData['time'] = str(datetime.datetime.now())
    snsData['msg'] = instanceId +" has been scheduled for a snapshot."
    snsData['instances'] = runningInstances

    #publish a SNS message that will trigger the ebs-snapshot-queue function
    response = sns.publish(
        TargetArn=ddsnsArn,
        Message=json.dumps(snsData))

    #publish a SNS message that will notify datadog of the impending snapshots
    ddresponse = sns.publish(
        TargetArn=snsArn,
        Message=json.dumps(snsData))
    
    return snsData

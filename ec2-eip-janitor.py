import boto3

def lambda_handler(event, context):
    contextVariables = context.invoked_function_arn
    contextVariables = contextVariables.split(":")
    region = contextVariables[3]
    accountId = contextVariables[4]

    client = boto3.client('ec2', region_name=region)
    addresses_dict = client.describe_addresses()

    list_to_clean = []

    for eip_dict in addresses_dict['Addresses']:
        if 'AssociationId' in eip_dict:
            print "the AssociationID for " + eip_dict['PublicIp'] +" exists"
        else:
            print "the AssociationID for " + eip_dict['PublicIp'] +" does not exist!"
            list_to_clean.append(eip_dict)

    numberToClean = len(list_to_clean)
    print "Number of EIPs to clean: " + str(numberToClean)
    print "The list of EIPs to clean:"
    print list_to_clean

    for eip in list_to_clean:
        response = client.release_address(
            DryRun=False,
            AllocationId=eip['AllocationId'])
        print "The EIP : " + eip['PublicIp'] + " was successfully cleaned"
        print response

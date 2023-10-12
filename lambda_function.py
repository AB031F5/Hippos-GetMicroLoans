import json
import random
import decimal 
import boto3
import random
import datetime
from datetime import timedelta


loansTable = 'loanTable'
customersTable = 'customerTable'

def get_slots(intent_request):
    return intent_request['sessionState']['intent']['slots']
    
def get_slot(intent_request, slotName):
    slots = get_slots(intent_request)
    if slots is not None and slotName in slots and slots[slotName] is not None:
        return slots[slotName]['value']['interpretedValue']
    else:
        return None    

def get_session_attributes(intent_request):
    sessionState = intent_request['sessionState']
    if 'sessionAttributes' in sessionState:
        return sessionState['sessionAttributes']

    return {}

def elicit_intent(intent_request, session_attributes, message):
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'ElicitIntent'
            },
            'sessionAttributes': session_attributes
        },
        'messages': [ message ] if message != None else None,
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }


def close(intent_request, session_attributes, fulfillment_state, message):
    intent_request['sessionState']['intent']['state'] = fulfillment_state
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close'
            },
            'intent': intent_request['sessionState']['intent']
        },
        'messages': [message],
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }

def CheckBalance(intent_request):
    # check for loan balance
    session_attributes = get_session_attributes(intent_request)
    slots = get_slots(intent_request)
    account = get_slot(intent_request, 'accountNumber')
    phone = get_slot(intent_request, 'phoneNumber')
    #Query to get account information
    balance = str(checkForAccountInfoWithLoanAccount(int(account), phone))
    
    text = balance
    message =  {
            'contentType': 'PlainText',
            'content': text
        }
    fulfillment_state = "Fulfilled"    
    return close(intent_request, session_attributes, fulfillment_state, message)   

def FollowupBalance(intent_request):
    # check for loan balance
    session_attributes = get_session_attributes(intent_request)
    slots = get_slots(intent_request)
    account = get_slot(intent_request, 'accountNumber')
    phone = get_slot(intent_request, 'phoneNumber')
    balance = str(checkForAccountInfoWithLoanAccount(int(account), phone))
    text = balance
    message =  {
            'contentType': 'PlainText',
            'content': text
        }
    fulfillment_state = "Fulfilled"    
    return close(intent_request, session_attributes, fulfillment_state, message)
    
def dispatch(intent_request):
    # base function to handle intents and actions
    intent_name = intent_request['sessionState']['intent']['name']
    response = None
    # Dispatch to your bot's intent handlers
    if intent_name == 'CheckLoanLimit':
        return CheckBalance(intent_request)
    elif intent_name == 'FollowupBalance':
        return FollowupBalance(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')

def lambda_handler(event, context):
    response = dispatch(event)
    #return checkForAccountInfoWithLoanAccount(5801234567, '2567')
    #return update_item_increment_value(3920038301, '200')
    return response
    
def checkForAccountInfo(accountNumber, phoneNumber):
    # query against acc, phone
    dynamoDb =boto3.resource('dynamodb')
    cTb = dynamoDb.Table('customerTable')
    response = cTb.get_item(Key={'accountNumber':accountNumber})
    phoneN = response['Item']['phoneNumber']
    amountEligible = response['Item']['amountEligible']
    try:
        if phoneN != '':
            if str(phoneNumber) == phoneN[-4:]:
                comment = response['Item']['comment']
                if amountEligible == '0' and comment == '':  
                    return "Please note you have an existing loan."
                elif amountEligible == '0' and comment != '':   
                    return comment
                else:
                    return 'You have a loan limit of '+amountEligible+' Ugx. Do you want to continue and get a loan?'
            else:
                return 'Unknown account'
        else:
            return 'Sorry, unable to process your request'
    except KeyError as e:
        raise e

def checkForAccountInfoWithLoanAccount(accountNumber, phoneNumber):
    # query against acc, phone
    dynamoDb =boto3.resource('dynamodb')
    cTb = dynamoDb.Table('customerTable')
    response = cTb.get_item(Key={'accountNumber':accountNumber})
    phoneN = response['Item']['phoneNumber']
    amountEligible = response['Item']['amountEligible']
    loanAccount = response['Item']['lastName']
    
    try:
        if phoneN != '':
            if str(phoneNumber) == phoneN[-4:]:
                return checkForAccountBalance(int(loanAccount))
            else:
                return 'Unknown account'
        else:
            return 'You qualify for a loan'
    except KeyError as e:
        raise e

def checkForAccountBalance(accountNumber):
    # query against acc, phone
    dynamoDb =boto3.resource('dynamodb')
    cTb = dynamoDb.Table('loanTable')
    response = cTb.get_item(Key={'loanAccount':accountNumber})
    loanBal = response['Item']['loanBalance']
    loanStat = response['Item']['loanStatus']
    try:
        if loanStat == 'Pending' and loanBal != '0':
            if loanBal != '':
                text = "Thank you. The balance on your "+str(accountNumber)+" account is "+str(loanBal)+" Ugx."
                return text
            elif loan == '0':
                text = "Thank you. Your loan balance "+str(loanBal)+" Ugx."
                return text
            else:
                return 'Sorry, unable to process your request'
        else:
            return 'Thank you for clearing your loan balance on time'
    except KeyError as e:
        raise e
    
    
def addLoanAccount():
    # create loan account
    loanAccountNumber = random.randrange(3000000000, 3999999999)
    today = datetime.date.today()
    date_1 = datetime.date.strftime(today, '%m-%d-%Y')
    result = today + timedelta(days=30)
    
    dynamoDb =boto3.resource('dynamodb')
    loanTb = dynamoDb.Table('loanTable')
    response = loanTb.put_item(
        Item = {
        'loanAccount':loanAccountNumber,
        'disbursementDate':str(today),
        'loanAmount':'70000',
        'interestFees':'0',
        'loanBalance':'5000',
        'repaymentDate':str(result),
        'loanStatus':'Pending',
        'accountNumber':'5801234567'
        })
    return response

def disburseLoan(lnAccount, loan):
# disburse loan
    today = datetime.date.today()

    dynamoDb =boto3.resource('dynamodb')
    loanTb = dynamoDb.Table('loanTable')
    response = loanTb.update_item(
        Key={"loanAccount": int(lnAccount)},
        UpdateExpression="set loanAmount = :loan",
        ExpressionAttributeValues={
            ":loan": int(loan),
        },
        ReturnValues="UPDATED_NEW",
    )
    response2 = loanTb.update_item(
        Key={"loanAccount": int(lnAccount)},
        UpdateExpression="set loanBalance = :loan",
        ExpressionAttributeValues={
            ":loan": int(loan),
        },
        ReturnValues="UPDATED_NEW",
    )
        
    response3 = loanTb.update_item(
        Key={"loanAccount": int(lnAccount)},
        UpdateExpression="set disbursementDate = :dateOfDisbursement",
        ExpressionAttributeValues={
            ":dateOfDisbursement": str(today),
        },
        ReturnValues="UPDATED_NEW",
    )
    
    return response

    # output

    # {'total_orders': Decimal('11')}

def addAccount():
    
    dynamoDb =boto3.resource('dynamodb')
    customerTb = dynamoDb.Table('customerTable')
    response = customerTb.put_item(
        Item = {
        'accountNumber':58888888800,
        'firstName':'Dison',
        'lastName':'Lyada',
        'amountEligible':'0',
        'phoneNumber':'0789565898',
        'comment':''
        })
    return response
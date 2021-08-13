import logging
import json
import os
import base64
import azure.functions as func
import uuid
import io
import tempfile
import time
import math
from datetime import datetime

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from msrest.exceptions import HttpOperationError
from PIL import Image

#TODO : Put in Application Settings
#os.environ["myAppSetting"]
#subscription_key = "ece422658f8b4cdd80f45d4aec0865f8"
#endpoint = "https://ftagov-vision.cognitiveservices.azure.us"
#db_breaker = pybreaker.CircuitBreaker(fail_max=10, reset_timeout=60)

#Default values
DEFAULT_VISION_TPS = 10 #Vision limit of transactions per second. NOTE: This is for POSTs and GETs batch count
DEFAULT_VISION_TPS_SECONDS = 1 #how many seconds for transactions
DEFAULT_RETRY_COUNT = 5
DEFAULT_TIMEOUT_MILLISECONDS = 1000
DEFAULT_INVALID_IMAGE = "INVALID_IMAGE"


subscription_key = None
endpoint = None
VISION_TPS = None
VISION_TPS_SECONDS = None
RETRY_COUNT  = None
TIMEOUT_MILLISECONDS = None
INVALID_IMAGE = None


def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    initialize_environment()

    try:
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )
    
    if body:
        logging.info("Processing Image")
        result = compose_response(body)
        return func.HttpResponse(result, status_code=200, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def initialize_environment():
    global subscription_key
    global endpoint
    global VISION_TPS
    global VISION_TPS_SECONDS
    global RETRY_COUNT 
    global TIMEOUT_MILLISECONDS
    global INVALID_IMAGE
    if(subscription_key is None):
        #global subscription_key
        subscription_key = os.environ['OCR_SUBSCRIPTION_KEY']
    

    if(endpoint is None):

        endpoint = os.environ['OCR_ENDPOINT']

    #Assign Default values if not available
    if(VISION_TPS is None or 
        VISION_TPS_SECONDS is None or 
        RETRY_COUNT is None or 
        TIMEOUT_MILLISECONDS is None or
        INVALID_IMAGE is None) :

        #global VISION_TPS_SECONDS
        #global VISION_TPS
        #global RETRY_COUNT
       # global TIMEOUT_MILLISECONDS
       # global INVALID_IMAGE

        try:
            VISION_TPS = os.environ['OCR_VISION_TPS']
        except KeyError  as error:
            VISION_TPS = DEFAULT_VISION_TPS
        try:
            VISION_TPS_SECONDS = os.environ['OCR_VISION_TPS_SECONDS']
        except KeyError  as error:
            VISION_TPS_SECONDS = DEFAULT_VISION_TPS_SECONDS
        try:
            RETRY_COUNT = os.environ['OCR_RETRY_COUNT']
        except KeyError  as error:
            RETRY_COUNT = DEFAULT_RETRY_COUNT
        try:
            TIMEOUT_MILLISECONDS = os.environ['OCR_TIMEOUT_MILLISECOND']
        except KeyError  as error:
            TIMEOUT_MILLISECONDS = DEFAULT_TIMEOUT_MILLISECONDS
        try:
            INVALID_IMAGE = os.environ['OCR_INVALID_IMAGE']
        except KeyError  as error:
            INVALID_IMAGE = DEFAULT_INVALID_IMAGE


    
    logging.info(f"Setting VISION_TPS = {VISION_TPS}.")
    logging.info(f"Setting VISION_TPS_SECONDS = {VISION_TPS_SECONDS}.")
    logging.info(f"Setting RETRY_COUNT = {RETRY_COUNT}.")
    logging.info(f"Setting TIMEOUT_MILLISECONDS = {TIMEOUT_MILLISECONDS}.")
    logging.info(f"Setting INVALID_IMAGE = {INVALID_IMAGE}.")

def compose_response(json_data):
    values = json.loads(json_data)['values']

    # Prepare the Output before the loop
    results = {}
    operations = {}
    results["values"] = []
    operations["Ids"] = []
    batch_count = VISION_TPS
    logging.info(f"Received {len(values)} records and processing.....")
    #https://docs.microsoft.com/en-us/azure/search/cognitive-search-concept-image-scenarios#sample-skillset
    for value in values:

        try:
            recordId = value['recordId']
            logging.info(f"Received record {recordId}")
        except AssertionError  as error:
            return None

        assert ('data' in value), "'data' field is required."
        data = value['data']
        base64String = data["image"]["data"]
        #Tested with passing URL
        #url = data["image"]["url"]
        base64Bytes = base64String.encode('utf-8')
        inputBytes = base64.b64decode(base64Bytes)

        #Build temp image file for writing
        r_uuid = str(uuid.uuid4()).replace('-', '')
        name = 'image{0}.jpg'.format(r_uuid)
        temp = tempfile.gettempdir()

        
        outfilename = os.path.join(temp, name)
        logging.info(f"Writing to file {outfilename}")
        image = inputBytes     

        img = Image.open(io.BytesIO(image))
        img.save(outfilename, 'jpeg')

        #read the file to stream to API
        #note: tried cv2.imdecode and had max limit errors. See below:
        with open(outfilename, "rb") as read_image:
            operations = sendReadAPI(read_image , recordId, operations)
            
        try:
            os.remove(outfilename)
        except IOError as e:
            logging.warning(f"Error deleting file {outfilename}")

        #############################
        #STREAM NEED TO DEBUG
        # Use numpy to convert the string to an image
        #jpg_as_np = np.frombuffer(inputBytes, dtype=np.uint8)
        
        #img = cv2.imdecode(jpg_as_np, flags=1)
        #originalImage = cv2.imdecode(jpg_as_np, flags=1) # reads data from memory cache coverts into image format
        #buf = cv2.imencode('.jpg', jpg_as_np) #converts image into streaming data
        #################Send to Vision##########################
        

        ############Computer Vision Client ##############################################################
        #Needs to be this format
        #https://docs.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-web-api
        #Send  in Batches: Example 10 POSTs and then 10 GETs(Vision API results)
        
        
        batch_count -=1
        logging.info(f"Batch Count for sending to API {batch_count}")
        if(batch_count <= 0) :
            logging.info(f"Batch Count: {batch_count} for the following ids:{operations}")
            results = processBatchOperations(operations, results)
            operations["Ids"] = [] #clear the operations for the next batch
            batch_count = VISION_TPS

        #logging.info(f"Results: {output}")
        
    #process the rest of the request if they are available
    if(operations is not None and len(operations) > 0):
        results = processBatchOperations(operations, results)
        operations["Ids"] = []
    #logging.debug(results)
    
    return json.dumps(results, ensure_ascii=False)

def sendReadAPI(read_image,recordId, operations):
    
    retries = RETRY_COUNT
    start_time = datetime.now()
    computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

    '''
    OCR: Read File using the Read API, extract text - local
    This example extracts text from a local image, then prints results.
    This API call can also recognize remote image text (shown in next example, Read File - remote).
    '''
    # Call API with image and raw response (allows you to get the operation location)
    logging.info(f"Stream File to Vision API endpoint")

    while retries > 0 :
        read_response = None
        try:
            
            read_response = computervision_client.read_in_stream(read_image, raw=True)
            #read_response = callAPIHelper(read_image, computervision_client)
            retries = RETRY_COUNT
            #Tested with URL
            #read_response = computervision_client.read(url,raw=True )
            #operations = parseLocation(recordId, operations, read_response)

        except HttpOperationError as e:
            if(e.response.status_code == 429): #TODO:Log error when retries over retry count
                #response = e.Response
                logging.info(f"Error: Too many requests. Retry count:{retries}")
                start_time = delay(start_time)
                retries -=1
                #Will receive a 400 error on subsequent requests. Seek to the beginning of the file. 
                read_image.seek(0)
                continue
            elif(e.response.status_code == 400):
                logging.info("Error: {0}  Response: {1}".format(e.message, e.response.content))
                logging.warning("This image error will be ignored. Will try to get the location anyway")
                
            else:
                logging.warning("Unknown error: {0} \n Retry count{1}".format(e.message), retries)
                retries -=1
                continue
        operations = parseLocation(recordId, operations, read_response)
         
        break
    return operations

def parseLocation(recordId, operations, read_response):

    if(read_response is None):
        logging.warning(f"Error with read response is null. Record id {recordId}")
        operations["Ids"].append({
         "RecordId": recordId,
         "Id": INVALID_IMAGE
        })
        return operations

    # Get the operation location (URL with ID as last appendage)
    read_operation_location = read_response.headers["Operation-Location"]

    logging.info(f"Calling Read API: {read_operation_location}")
    # Take the ID off and use to get results
    operation_id = read_operation_location.split("/")[-1]

    operations["Ids"].append({
         "RecordId": recordId,
         "Id": operation_id
    })
    logging.info(f"Received operation id {operation_id}")
    return operations

def processBatchOperations(operations, results): 
    retries = RETRY_COUNT
    start_time = datetime.now()

    #TODO: Clean up
    computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))
    # Call the "GET" API and wait for the retrieval of the results
    for operation in operations["Ids"]: #operation_ids:

        try:
            operation_id = operation['Id']
            record_id = operation['RecordId']
        except AssertionError  as error:
            break

        if(operation_id == INVALID_IMAGE):
            logging.info(f"Returning null information for Record {record_id}")
            results = emptyRecordId(results, record_id)
            continue #go to next record
        while retries > 0 :
            try:
                #process the data
                logging.info(f"Begin parsing operation {operation_id} for record id {record_id}. Retry {5-retries} of {RETRY_COUNT}")
                read_result = computervision_client.get_read_result(operation_id)
                logging.info(f"Response for the read result {read_result.status.lower()}")
                #Checking if results are available, if not will retry
                if read_result.status.lower() not in ['notstarted', 'running']:
                    retries = RETRY_COUNT #restart count

                    #read_result = computervision_client.get_read_result(operation_id)
                    #read_result = callAPIHelper(operation_id, computervision_client)

                    #Add results, line by line
                    if read_result.status == OperationStatusCodes.succeeded:
                        #print(json.dumps(read_result.analyze_result.read_results))
                        for text_result in read_result.analyze_result.read_results:

                            language = text_result.language
                            all_text = ""
                            text = ""
                            lines = []
                            words = []
                            for line in text_result.lines:
                                all_text = '{0} \n{1}'.format(all_text, line.text)
                                #text
                                
                                lines.append({
                                    "boundingBox" : line.bounding_box,
                                    "text": str(line.text)
                                })
                                for word in line.words:
                                    words.append({
                                    "boundingBox" : word.bounding_box,
                                    "text": str(word.text)
                                })
                                
                            logging.info(f"Processing record {record_id}")#" with lines: {lines}")
                            logging.info(f"All Text: {all_text[:25]}")
                            results["values"].append({
                                "recordId": record_id,   
                                "data": {
                                    "text": all_text,
                                    "layoutText":
                                    {
                                        "language": str(language),
                                        "text" : all_text,
                                        "lines": lines,
                                        "words" : words
                                    }

                                }
                            })
                        break #get out of retry loop
                    
                elif(retries <=1): # last retry, process the request with empty info and continue to the next record
                    logging.warning(f"Record id {record_id} exceeded retries")
                    results = emptyRecordId(results, record_id)
                    break
                else: #retry the same record
                    start_time = delay(start_time)
                    retries -=1
                    continue 


            except HttpOperationError as e: #TODO: Change this to return nothing
                logging.warning(f"Error for Operation Id {operation_id}: {e.message}")
                retries -=1
                if retries < 0:
                    results = emptyRecordId(results, record_id)
                    logging.warning("MAX RETRIES EXCEEDED") 
                    break
                continue #retry again
    return results
'''
   Use for records that errored. Skill expects record id. 
   Add the record and empty strings for the text and layout text
'''
def emptyRecordId(results, record_id):
    results["values"].append({
                "recordId": record_id,   
                "data": {
                    "text": "",
                    "layoutText":
                    {
                        "language": "",
                        "text" : "",
                        "lines": [],
                        "words" : []
                    }
                }
            })
    return results
#ComputerVisionOcrErrorException

#@circuit(failure_threshold=10, recovery_timeout=60)
#@db_breaker
'''def callAPIHelper(operation_id, computervision_client):
    read_result = computervision_client.get_read_result(operation_id)
    return read_result
'''
def delay(start_time):

    #Time difference in milliseconds
    time_diff_sec = datetime.now() - start_time
    secs = time_diff_sec.total_seconds()
    msecs = secs * 1000
    logging.info(f"Milliseconds occurred {msecs}")

    #Sleep until our TPS limitation is expired
    logging.info(f'Waiting {math.ceil(TIMEOUT_MILLISECONDS - (msecs % TIMEOUT_MILLISECONDS))} milliseconds.....')
    time.sleep((TIMEOUT_MILLISECONDS - (msecs % TIMEOUT_MILLISECONDS))/1000)
    
    return datetime.now() #start our time over for delay
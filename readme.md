# CogSearchFunction
This solution contains 2 Function Apps that performs the following:
- Compress large PDF Files
- Process images from PDF pages for OCR

<br/>

## PDF Compression Function App
<br/>
The Function App tier needs to be Premium or more to support [VNET integration and Private Endpoint](https://docs.microsoft.com/en-us/azure/azure-functions/functions-premium-plan?tabs=portal#available-instance-skus). This has been tested with P3v3. Since these are large file, a increase in resources is required to process these files. You may adjust these as needed. 

This solution has 2 options for deployment: 
- Publish code directly
- Container

>TODO: Need to test with 3.9
Version: Python 3.8. <br/><br/>

### Publish Code

The following line in _init_.py will install Ghostscript when not using containers. 

```
command = subprocess.run(["apt-get", "-y", "install", "ghostscript"], check=True)
```
> Note this should not execute if using Docker container, but it is still tested if Ghostscript is installed.

<br/><br/>
### Container

The code contains a DOCKERFILE that can be used with deploying to a Function App container. The file installs Ghostscript with the following command: 

```
  RUN sudo apt-get -y install ghostscript 
  ```


**Build the requirements.txt** (This step is optional since the requirements.txt file is already provided)

```
  pip install ghostscript==0.7
  pip freeze > requirements.txt
```

**Create ACR**
- Enable Admin user under the Access Keys blade


**Build Image Locally**

``` 
docker build --no-cache --tag pdfmodpython.azurecr.io/pdfcompression:latest .
```

**Push to ACR**

```
  az acr login --name acr_name
  docker push  acr_name.azurecr.io/pdfcompression:latest
  ```

**Create Function App with Container** (Note: need to more computer resources to execute process: EP3)**
- Deployment Center Blade -> Use Container Registry
- Fill out the settings and turn on "Continuous Deployment"
- Add the Storage Connection String to your App Settings. 
  
 **Don't forget to add the settings for the storage**
` func settings add AzureWebJobsStorage "<string>"`

<br/>

## OCR Custom Web API Skill
<br/>

The function app will process images obtained from the output from a previous skill. The output will be the text received from the OCR processed via the Vision API. There is a shared OCR Skill Out-of-the-Box solution. It does not support Private Endpoint, which is the reason for this custom Web API Skill. The following information will describe the function app in more detail. 

<br/>

The Function App tier needs to be Premium or more to support [VNET integration and Private Endpoint](https://docs.microsoft.com/en-us/azure/azure-functions/functions-premium-plan?tabs=portal#available-instance-skus). 

<br/>

TODO: The following configurations are pulled from the Function App configuration. Each one explained below. 
- **SUBSCRIBTION_KEY** - Key to access to Vision API
- **VS_ENDPOINT** - Endpoint for the Computer Vision API. Example: https://{cog-search-name}.cognitiveservices.azure.us
- **VISION_TPS** - Transactions per second. The default is 10 TPS. This value could change in the future or you increase the 10 TPS limit through a support ticket. See [costs](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/computer-vision/). 
- **RETRY_COUNT** - With the 10 TPS limit, you will experience a "Too many requests" or 429 warning. This is expected and not logged as an error. The next call will wait until the next second to try again. See TIMEOUT_MILLISECONDS. Default is 5 retries. 
- **TIMEOUT_MILLISECONDS** - The time to delay. This default is 1000 or 1 second. If 10 requests are sent to the Vision API and a 429 warning occurs, then the app will delay until the next second or TIMEOUT_MILLISECONDS. For example, 10 requests took 350 milliseconds, then the next retry will occur 1000 - 350 = 650 msecs. A delay of 650 msecs occurs. If TIMEOUT_MILLISECONDS is decrease to much, then the retries will be exausted. Remember we have a limit of 10 Transactions per Second. If this value is increased too much, then you risk the Function App timeout. 
> The [max timeout value](https://docs.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-interface#web-api-custom-skill-interface) is PT3M50S(3 Minutes 50 Seconds). This is configured in the Skillset for scaling. See [Common Error Messages](#Troubleshooting)

<br/>

On circumstances where retry exhaustion or other unknown errors is encountered, The record is returned in the output with the record id and empty values for the text and layoutText. The record id correlates to the image or PDF page. This allows the other records/image/page to be processed. For example, if there are 10 images, which are 10 pages, if #2 fails then 1 and 3-10 are still processed, but #2 will have empty results. This can be viewed from App Insights logs to determine the images that were not processed. This is defined in the **emptyRecordId** method in \_\_init\_\_.py file. 

<br/>

The following parameters can be configured for performance:
- **degreeOfParallelism**(Skill) - number of concurrent requests made to the skill. This is located in the JSON configuration. [See documentation for parameters](https://docs.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-web-api)
- **batchSize**(Skill and Indexer) - Number of records to process sent to the skill. This is located in the JSON configuration. [See documentation for sample Custom Web API skill](https://docs.microsoft.com/en-us/azure/search/cognitive-search-concept-image-scenarios#sample-skillset)
- **FUNCTIONS_WORKER_PROCESS_COUNT** - Workers on the Function App to help with processing http requests. The is located in the app configuration of the Function App. The default depends on the [Python version](https://docs.microsoft.com/en-us/azure/azure-functions/python-scale-performance-reference#set-up-max-workers-within-a-language-worker-process). The [max is 10](https://docs.microsoft.com/en-us/azure/azure-functions/functions-app-settings#functions_worker_process_count). This solution has been tested with 5. 

<br/>

> Currently, you have a limit of 10 Transactions per Second

<br/>

See documentation for additional information: [Skill Setting](https://docs.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-scale#skill-settings)

<br/>

#### Function Output

The Function App output is in the following format:

```
{
    "values"
    [{
       "recordId": "record id",   
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
    }]
}
```

### Deployment

TODO:

<br/>

### Troubleshooting

[See Common Error Messages](https://docs.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-scale#common-error-messages) and [Best Practices](https://docs.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-scale#best-practices)

<br/>

### Considerations


<br/>
<br/>
#### Multi-Threaded

<br/>

This python app is single-threaded. If need to process a substantially amount of Transactions per Second, then create a support ticket to increase the limit and may need to refactor the current application for async operations. Currently, the application far exceeds the 10 TPS limation. See [Performance-specific configurations](https://docs.microsoft.com/en-us/azure/azure-functions/python-scale-performance-reference#performance-specific-configurations)

<br/>

#### Design Patterns 

<br/>

Currently, the Retry Pattern is implemented to aid with the 429 errors. The [Circuit Breaker Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker) is not implemented in this solution. The [Circuit Breaker Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker) is typically for establishing connections in long-live environments and to prevent exhausting the service with multiple calls. The Retry Pattern will suffice for this solution since it is typically use for short-live environments like Function Apps. If there is a need for a longer execution times, consider the [Circuit Breaker Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker). 

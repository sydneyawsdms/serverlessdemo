# Solution

## This is the solution we are going to implement

![](https://github.com/sydneyawsdms/serverlessdemo/blob/master/solution.jpg?raw=true)


1. Upload the photo of a celebrity.

1. Binary data is POSTed to API Gateway.

1. API Gateway passes the data to Lambda (base64-encoded).

1. Lambda converts it back to binary and invokes [RecognizeCelebrities](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rekognition.html#Rekognition.Client.recognize_celebrities).

1. Name and Confidence are returned back to the client.


## And these are the main steps to implement it

1. Create the Lambda role in IAM with these two Managed Policies: AWSLambdaBasicExecutionRole and AmazonRekognitionFullAccess.

1. Create the Lambda function in a language of your choice.

1. Create API Gateway API with a POST method and attach Lambda to it.
    * Remember: Content-Type will be image/jpeg.
    * Don't forget to enable binary support and CORS.
    * Mapping template is: {"picture": "$input.body"}

1. Update the HTML page 'celebrity.html' with your API URL and test.

----

# Extra challenges for the savvy
*We created 6 extra challenges that can be built on top of the basic solution. Feel free to try to implement as many as you can in no particular order.*

## URL to celebrity's page
The API call RecognizeCelebrities sometimes returns a URL with a link to a webpage for the celebrity. The challenge is to modify the initial solution to pass this URL back to the HTML page and make the celebrity's name clickable there. Something like:

`Name: [Charlize Theron](https://www.imdb.com/name/nm0000234/)`

We suggest to create a new resource in API Gateway rather than modifying the current one.

## Recognise multiple celebrities
The API call RecognizeCelebrities can actually recognise multiple celebrities from a single photo. Amend the resources involved to pass the list of recognised celebrities back to the HTML page and list them all there. Something like:

```
Name: Charlize Theron
Confidence: 100%

Name: Brad Pitt
Confidence: 89%
```

We suggest to create a new resource in API Gateway rather than modifying the current one.

## Lambda Proxy Integration
Create a new resource in API Gateway with a POST method that points to the same Lambda function as the original solution: but this time using a proxy integration. Then amend the Lambda function to be able to correctly handle both proxy and non-proxy integration.

## Without Lambda
API Gateway can actually invoke Rekognition directly, without the need for Lambda. Create a new resource in API Gateway and implement the same solution without Lambda.

## Lambda in VPC
Enable VPC support for Lambda. Then make the necessary configuration to ensure Lambda is still able to invoke Rekognition.

## Read out the celebrity's name
Once the name of the celebrity is returned by Rekognition, pass it to [Amazon Polly](https://aws.amazon.com/polly/) to have it spelt out in the HTML page.

# How we collect the challenges
Each candidate will have to provide the following information:
* Lambda functions code
* Screenshot of the *Integration Request*
* Mapping templates used on *Integration Request* and *Integration Response*
* *API Gateway logs* for a successful *RequestId* (text file, you can copy from CloudWatch)

Deliverables must be sent to the email: [syd-ana-l2h@amazon.com](mailto:syd-ana-l2h@amazon.com) along with the following information:
* Candidate name
* Candidate ID

----
**Good luck!!**
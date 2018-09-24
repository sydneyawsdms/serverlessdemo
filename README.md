# Solution

## This is the solution discussed

![](https://github.com/sydneyawsdms/serverlessdemo/blob/master/solution.jpg?raw=true)

1. Upload the photo of a celebrity.
1. Binary data is POSTed to API Gateway.
1. API Gateway passes the data to Lambda (base64-encoded).
1. Lambda converts it back to binary and invokes [RecognizeCelebrities](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rekognition.html#Rekognition.Client.recognize_celebrities).
1. Name and Confidence are returned back to the client.

## And these are the main steps to implement it

1. Create the Lambda role in IAM with these two Managed Policies: AWSLambdaBasicExecutionRole and AmazonRekognitionFullAccess.

1. Create the Lambda function in Python 3.6.

1. Create API Gateway API with a POST method and attach Lambda to it.
    * Remember: Content-Type will be image/jpeg.
    * Don't forget to enable binary support and CORS.
    * Mapping template is: {"picture": "$input.body"}

1. Update the HTML page with your API URL and test.

----

## Extra challenges for the savvy

*coming soon...*
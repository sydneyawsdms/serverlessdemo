var AWS = require('aws-sdk');
AWS.config.update({ region: process.env.AWS_REGION });
var DDB = new AWS.DynamoDB({ apiVersion: "2012-10-08" });
const tablename = process.env.TABLE_NAME;
var translate = new AWS.Translate({ apiVersion: '2017-07-01' });
var comprehend = new AWS.Comprehend();

require('aws-sdk/clients/apigatewaymanagementapi');

var apigwManagementApi;

async function wsconnect(connectionId, nickname) {
  var putParams = {
    TableName: tablename,
    Item: {
      connectionId: { S: connectionId }
    }
  };
  if (nickname) {
    putParams.Item.nickname = { S: nickname }
  }
  await send_messages("", { "message": "Joined the chatroom", "nickname": nickname });
  await DDB.putItem(putParams).promise();
}

async function ws_disconnect(connection_id) {
  var scanParams = {
    FilterExpression: "connectionId = :a",
    ProjectionExpression: "nickname",
    TableName: tablename,
    ExpressionAttributeValues: {
      ":a": {
        S: connection_id
      }
    }
  };
  var nicknames = await DDB.scan(scanParams).promise();
  var deleteParams = {
    TableName: tablename,
    Key: {
      connectionId: { S: connection_id }
    }
  };
  await DDB.deleteItem(deleteParams).promise();
  console.log(JSON.stringify(nicknames));
  const nickname = (nicknames.Items[0].hasOwnProperty('nickname')) ? nicknames.Items[0].nickname.S : "";

  await send_messages(connection_id, { 'nickname': nickname, 'message': "left the chatroom" });
}

async function send_messages(current_connection, message, to_name) {
  message.timestamp = Date.now()/1000;
  var scanParams = {
    TableName: process.env.TABLE_NAME,
    ProjectionExpression: "connectionId"
  };

  if (to_name) {
    scanParams.FilterExpression = "nickname = :a",
      scanParams.ExpressionAttributeValues = {
        ":a": {
          S: to_name
        }
      }
  }

  var connections = await DDB.scan(scanParams).promise();
  var promises = [];
  connections.Items.forEach(function (element) {
    promises.push(new Promise(function (resolve, reject) {
      var sentMessage = JSON.parse(JSON.stringify(message));
      if (element.connectionId.S == current_connection) {
        sentMessage.nickname = "You";
      }
      var post_data = {
        Data: JSON.stringify(sentMessage),
        ConnectionId: element.connectionId.S
      };
      apigwManagementApi.postToConnection(post_data, (err, data) => {
        if (err) {
          ws_disconnect(element.connectionId.S);
          reject(err);
        } else {
          resolve(data);
        }
      });
    }));
  });
  await Promise.all(promises).then(function (values) { }).catch(function (values) {
    console.log(values);
  });
}

async function ws_message(connection_id, eventBody) {
  var eventBodyJson = JSON.parse(eventBody);

  if (eventBodyJson.translate) {
    var translateParams = {
      SourceLanguageCode: 'auto', /* required */
      TargetLanguageCode: 'en', /* required */
      Text: eventBodyJson.message
    };
    try {
      var translatedata = await translate.translateText(translateParams).promise();
      eventBodyJson.message = translatedata.TranslatedText;
    }
    catch (err) {
      console.log("translate failed...still use the original one");
    }
  }

  var post_data = {
    'message': eventBodyJson.message,
    'nickname': eventBodyJson.nickname
  }

  if (eventBodyJson.sentiment) {
    var params = {
      LanguageCode: 'en',
      Text: eventBodyJson.message
    };
    try {
      var comprehenddata = await comprehend.detectSentiment(params).promise();
      post_data.sentiment = comprehenddata.Sentiment;
    }
    catch (err) {
      console.log("detectSentiment failed...still use the original one");
    }
  }
  
  if (post_data.message.startsWith("@")) {
    var splitWords = post_data.message.split(" ");
    const to_name = splitWords.shift();
    post_data.message = splitWords.join(" ");
    await send_messages(connection_id, post_data, to_name.slice(1, to_name.length))
  } else {
    await send_messages(connection_id, post_data);
  }
}

exports.handler = async (event) => {
  if (!apigwManagementApi) {
    apigwManagementApi = new AWS.ApiGatewayManagementApi({
      apiVersion: "2018-11-29",
      endpoint: event.requestContext.domainName + "/" + event.requestContext.stage
    });
  }

  if (event['requestContext']['eventType'] == 'CONNECT') {
    var nickname = (event.hasOwnProperty("queryStringParameters")) ? event['queryStringParameters']['nickname'] : ""
    await wsconnect(event.requestContext.connectionId, nickname);
    return {
      statusCode: 200,
      body: "Connected."
    };
  }

  if (event['requestContext']['eventType'] == 'DISCONNECT') {
    return ws_disconnect(event.requestContext.connectionId);
  }

  if (event['requestContext']['eventType'] == 'MESSAGE') {
    await ws_message(event.requestContext.connectionId, event.body);
    return {
      statusCode: 200,
      body: "message sent."
    };
  }
};


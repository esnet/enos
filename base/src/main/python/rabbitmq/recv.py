from net.es.enos.rabbitmq import ProcessTokenRequest
from net.es.enos.rabbitmq import BrokerInfo
from net.es.enos.rabbitmq import UUIDManager
from net.es.enos.rabbitmq import SSLConnection
from net.es.enos.rabbitmq import WriteMsgToFile

from org.python.core.util import StringUtil
from java.util import Hashtable


from com.rabbitmq.client import QueueingConsumer

#
# Created by davidhua on 7/3/14.
#

broker = BrokerInfo()
broker.setHost("localhost")
broker.setUser("david2")
broker.setPassword("123")
broker.setPort(5672) # Port 5671 for ssl
broker.setSSL(False) # True for no ssl

HOME_FILE = "/var/enos/users/admin"
permissions = Hashtable()

# Get name of queue to receive messages from from file.
uuidQueue = UUIDManager(HOME_FILE)
queueName = uuidQueue.checkUUID()
# Create connection and queue
factory = SSLConnection(broker).createConnection()
connection = factory.newConnection()
channel = connection.createChannel()

channel.queueDeclare(queueName, False, False, True, None)

try:
    consumer = QueueingConsumer(channel)
    # Declare as exclusive consumer of queue
    channel.basicConsume(queueName, True, "consumer", False, True, None, consumer)
    print " [*] Waiting for messages."
except IOError:
    print "Unable to connect to queue."
    connection.close()
    sys.exit(1)

writer = WriteMsgToFile(HOME_FILE)

while True:
    try:
        delivery = consumer.nextDelivery()
        message = delivery.getBody()
        message = StringUtil.fromBytes(message)
        token = message.split(":",1)[0]
        rest = message.split(":",1)[1]
        message = str(message)

        # If message is a "token_request", process request and add new token to hashmap
        if message[0:13] == ("TOKEN_REQUEST"):
            makeToken = ProcessTokenRequest(message, channel)
            tokenID = makeToken.sendToken()
            permissions.put(tokenID[0], tokenID[1])

        # Otherwise, check if message has valid token (token in hashmap). 
        # If so, accept message, then delete token from valid list.
        else:
            if permissions.containsKey(token):
                print (" [x] Received '" + rest + "' from: " + permissions.get(token))
                writer.writeMsg(rest, permissions.get(token)) #Write message to text file
                permissions.remove(token)
            else:
                print " ERROR: INVALID TOKEN PROVIDED IN MESSAGE"
    except BaseException:
        print "Consumer encountered an exception."
        channel.queueDelete(queueName)
        channel.close()
        connection.close()
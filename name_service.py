import os, pika, json, time, random

some_names = ["Andrew", "Josh", "Peter", "Owen", "Shalita", "Helen", "Natalie", "Simon", "Jamie"]

class Namer(object):
    def __init__(self, routes):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.exchange = "warren"
        self.channel.exchange_declare(exchange=self.exchange, type="topic")
        result = self.channel.queue_declare(exclusive=True)
        self.queue_name = result.method.queue
        for route in routes:
            self.channel.queue_bind(exchange=self.exchange,
                                    queue=self.queue_name,
                                    routing_key=route)
        
    def publish(self, route, data):
        self.channel.basic_publish(self.exchange, routing_key=route,
                             body=json.dumps(data),
                             properties = pika.BasicProperties(content_type="application/json"))  

    def process(self, ch, method, properties, body):
        obj = json.loads(body)
        self.publish(method.routing_key + ".rsp", {"first":random.choice(some_names)})
        print " [x] %r:%r" % (method.routing_key, body)

    def start(self):
        self.channel.basic_consume(self.process,queue=self.queue_name,no_ack=True)
        self.channel.start_consuming()

    def close(self):
        self.connection.close()


if __name__ == "__main__":
    logger = Namer(["Name.get"])
    try:
        logger.start()
    finally:
        logger.close()

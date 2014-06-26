import os, pika, json, time

seen_uuids = {}

class Logger(object):
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
        if "id" in obj:
            if obj["id"] in seen_uuids:
                if method.routing_key.endswith(".exit"):
                    seen_uuid = seen_uuids[obj["id"]]
                    seen_uuid["end"] = obj["time"]
                    if seen_uuid["end"] - seen_uuid["start"] > 20:
                        print " [y] Too LONG"
                        self.publish("alert.HelloWorld", {"warning":"UUID %s took to long" % (obj["id"]) })
                else:
                    self.publish("alert.HelloWorld", {"error":"Seen UUIDs %s muliple times" % obj["id"] })
            else:
                seen_uuids[obj["id"]] = {}
                seen_uuids[obj["id"]]["start"] = obj["time"]
        print " [x] %r:%r" % (method.routing_key, body)

    def start(self):
        self.channel.basic_consume(self.process,queue=self.queue_name,no_ack=True)
        self.channel.start_consuming()

    def close(self):
        self.connection.close()


if __name__ == "__main__":
    logger = Logger(["HelloWorld.#"])
    logger.start()
    logger.close()

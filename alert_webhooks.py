import os, pika, json, time, datetime
from pymongo import MongoClient

class AlertWatcher(object):
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
        self.mongoClient = MongoClient()
        self.mongoCol = self.mongoClient["alerts"]["alerts"]
            
    def publish(self, route, data):
        self.channel.basic_publish(self.exchange, routing_key=route,
                             body=json.dumps(data),
                             properties = pika.BasicProperties(content_type="application/json"))  

    def process(self, ch, method, properties, body):
        obj = json.loads(body)
        dbobj = {}
        dbobj["routing_key"] = method.routing_key
        dbobj["time"] = datetime.datetime.utcnow()
        
        if "warning" in obj:
            dbobj["msg"] = obj["warning"]
            dbobj["type"] = "warning"
        elif "error" in obj:
            dbobj["msg"] = obj["error"]
            dbobj["type"] = "error"

        self.mongoCol.insert(dbobj);


    def start(self):
        self.channel.basic_consume(self.process,queue=self.queue_name,no_ack=True)
        self.channel.start_consuming()

    def close(self):
        self.connection.close()


if __name__ == "__main__":
    logger = AlertWatcher(["alert.#"])
    logger.start()
    logger.close()



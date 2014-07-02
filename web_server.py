import cherrypy, os, pika, json, time, uuid, random

_curdir = os.path.join(os.getcwd(), os.path.dirname(__file__))
notes_dir = os.path.join(_curdir, 'static')
notes_file = os.path.join(notes_dir, "notes.html")
notes_css = os.path.join(notes_dir, "notes.css")
notes_jquery = os.path.join(notes_dir, "jquery-1.10.1.js")
#print notes_dir

class RabbitHole(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.exchange = "warren"
        self.channel.exchange_declare(exchange=self.exchange, type="topic")
        result = self.channel.queue_declare(exclusive=True)
        self.queue_name = result.method.queue
        self.collected_messages = []
        self.timeout = 0.6
        
    def publish(self, route, data):
        self.channel.basic_publish(self.exchange, routing_key=route,
                             body=json.dumps(data),
                             properties = pika.BasicProperties(content_type="application/json"))  

    def collect(self, routes):
        for route in routes:
            self.channel.queue_bind(exchange=self.exchange,
                                    queue=self.queue_name,
                                    routing_key=route)
        try:
            t1 = time.time()
            self.channel.basic_consume(self.process, self.queue_name)
            while True:
                if (time.time() - t1) > self.timeout:
                    break
                self.channel.connection.process_data_events()

            resp = {}
            while self.collected_messages:
                method, properties, body = self.collected_messages.pop(0)
                if method.routing_key not in resp:
                    resp[method.routing_key] = json.loads(body)
                    self.channel.basic_ack(method.delivery_tag)
            return resp
        finally:
            self.channel.cancel()

    def process(self, ch, method, properties, body):
        self.collected_messages.append((method, properties, body))

    def close(self):
        self.connection.close()

class HelloWorld(object):
    def index(self):
        try:
            id = str(uuid.uuid4()) 
            rh = RabbitHole()
            rh.publish("HelloWorld.index.enter", {"id":id, "headers":cherrypy.request.headers, "time": time.time()})
            rh.publish("Name.get", {})
            results = rh.collect(["Name.get.rsp"])
            if "Name.get.rsp" not in results:
                rh.publish("alert.HelloWorld", {"error":"Name not returned in required time"})
                return "Hello World"

            return "Hello " + results["Name.get.rsp"]["first"]
            
            
        except Exception as ex:
            print ex
        finally:
            #time.sleep(random.randint(10,30))
            rh.publish("HelloWorld.index.exit", {"id":id, "time":time.time()})
            rh.close()

    def popular_names(self):
        try:
            rh = RabbitHole()
            rh.publish("HelloWorld.popular_names.enter", {"headers":cherrypy.request.headers, "time": time.time()})
            return "Hello World"
        except Exception as ex:
            print ex
        finally:
            rh.publish("HelloWorld.popular_names.exit", {"time":time.time()})
            rh.close()
        

    index.exposed = True
    popular_names.exposed = True
    

config = {"/notes.html": {
    'tools.staticfile.on':True,
    'tools.staticfile.filename': notes_file },
          "/notes.css": {
              'tools.staticfile.on':True,
              'tools.staticfile.filename': notes_css },
          "/jquery.js" : {
              'tools.staticfile.on':True,
              'tools.staticfile.filename': notes_jquery }
      }

cherrypy.config.update({'server.socket_port':8085})
cherrypy.quickstart(HelloWorld(), "/", config)

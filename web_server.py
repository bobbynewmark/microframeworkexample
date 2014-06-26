import cherrypy, os, pika, json, time, uuid, random

_curdir = os.path.join(os.getcwd(), os.path.dirname(__file__))
notes_dir = os.path.join(_curdir, '../notes.html')
#print notes_dir

class RabbitHole(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.exchange = "warren"
        self.channel.exchange_declare(exchange=self.exchange, type="topic")

    def publish(self, route, data):
        self.channel.basic_publish(self.exchange, routing_key=route,
                             body=json.dumps(data),
                             properties = pika.BasicProperties(content_type="application/json"))  

    def collect(self, routes):
        pass

    def close(self):
        self.connection.close()

class HelloWorld(object):
    def index(self):
        try:
            id = str(uuid.uuid4()) 
            rh = RabbitHole()
            rh.publish("HelloWorld.index.enter", {"id":id, "headers":cherrypy.request.headers, "time": time.time()})
            return "Hello World"
        except Exception as ex:
            print ex
        finally:
            time.sleep(random.randint(10,30))
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
    
        

cherrypy.config.update({'server.socket_port':8085})
cherrypy.quickstart(HelloWorld(), "/", {"/notes.html":{'tools.staticfile.on':True, 'tools.staticfile.filename': notes_dir }})

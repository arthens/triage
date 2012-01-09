import zmq
import msgpack
import mongoengine
from mongoengine.queryset import DoesNotExist
from models import ErrorInstance, Error
import logging

# config
ZMQ_URI = "tcp://0.0.0.0:5001"
MONGO_URI = "mongodb://lcawood.vm"
MONGO_DB = "logs"

# zero mq
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.bind(ZMQ_URI)
socket.setsockopt(zmq.SUBSCRIBE, '')

# mongo
mongoengine.connect('logs', host='lcawood.vm')

# messagepack
unpacker = msgpack.Unpacker()

#logging
logging.basicConfig(level=logging.DEBUG)

# serve!
while True:
    unpacker.feed(socket.recv())
    for msg in unpacker:
        if type(msg) == dict:
            try:
                error = Error.create_from_msg(msg)
                error.save()
            except Exception, a:
                logging.exception('Failed to process error')

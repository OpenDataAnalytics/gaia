import json
import os
import signal
import traceback
from subprocess import Popen
from uuid import uuid4

import cherrypy
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage

from utils import log, debug, error

SERVER_KEY = os.getenv('GEOWEBSOCKETKEY', 'aV64EBFjhYbhkeW0ETPGv43KGvBCYdO2Pq')
MODU_DIR = os.path.dirname(os.path.abspath(__file__))
NODE_DIR = os.path.abspath(os.path.join(MODU_DIR, '../nodes'))

class TwoWayDict(dict):
    def __len__(self):
        return dict.__len__(self) / 2

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        dict.__setitem__(self, value, key)

    def __delitem__(self, key):
        value = self[key]
        dict.__delitem__(self, key)
        dict.__delitem__(self, value)

class WebSocketRouter(WebSocket):

    usermap = TwoWayDict()
    nodemap = TwoWayDict()
    funcmap = dict()
    nodemanager = None

    def opened(self):
        if WebSocketRouter.nodemanager is None:
            WebSocketRouter.nodemanager = NodeManager();

    @staticmethod
    def register(name, func):
        """Registers a handler function for a given name

        @param func: static function that takes a websocket and message,
            message is json decoded before passed to this function
        """
        WebSocketRouter.funcmap[name] = func

    def getSender(self):
        """If sender is registered node, returns the registered name
        If sender is user, returns user uuid
        If sender is not yet registered, a new uuid is assigned,
          stored in user map, and returned.
        """

        if self in WebSocketRouter.nodemap:
            return WebSocketRouter.nodemap[self]
        elif self not in WebSocketRouter.usermap:
            WebSocketRouter.usermap[self] = str(uuid4())
            debug("Added user py id: %s uuid: %s" % \
                  (str(id(self)), WebSocketRouter.usermap[self]))
        return WebSocketRouter.usermap[self]

    def received_message(self, textMessage):
        """m is a TextMessage of json with the structure
        { target: String, message: Mixed }

        For node messages, target is the user uuid or GEOWEBKEY
        for registering

        For user messages, key is a registered name of node or func
        """

        debug("Recieved: %s" % str(textMessage))
        try:
            data = json.loads(str(textMessage))
        except Exception:
            error("Decoding json %s \n%s" % (str(textMessage),
                                             traceback.format_exc()))
            return

        if 'target' not in data:
            error("No target in message %s " % str(textMessage))
            return;

        if 'message' not in data:
            data['message'] = ''

        target = data['target']
        message = data['message']

        if target == SERVER_KEY:
            debug("%s - %s - %s" % ('registering', str(id(self)), message))

            if message in WebSocketRouter.nodemap:
                error("Attempt to register existing name %s" % message)
                return;

            WebSocketRouter.nodemap[message] = self

            # send register message to all users
            registerData = {'target':'nodemanager', 'message': message }
            registerJSON = json.dumps(registerData)
            for ws in WebSocketRouter.usermap:
                if type(ws) is WebSocketRouter:
                    debug("Found one")
                    ws.send(registerJSON)

        elif target in WebSocketRouter.nodemap:
            debug("Sending to node id:%s" % \
                  str(id(WebSocketRouter.nodemap[target])))
            data['target'] = self.getSender()
            debug(str(WebSocketRouter.nodemap[target]))
            try:
                WebSocketRouter.nodemap[target].send(json.dumps(data))
            except Exception, e:
                error(" Function: %s\nSender: %s\nMessage: %s\nError: %s" % (
                        target, self.getSender(), message,
                        traceback.format_exc()))
                return

            debug("Sent")

        elif target in WebSocketRouter.usermap:
            debug("Sending to user")
            data['target'] = self.getSender()
            WebSocketRouter.usermap[target].send(json.dumps(data))

        elif target in WebSocketRouter.funcmap:
            self.getSender()  # places user in usermap if not already
            try:
                result = WebSocketRouter.funcmap[target](self, message)
                debug('performed func with result %s' % str(result))
                if result is not None:
                    JSON = json.dumps({'target':target, 'message': result})
                    self.send(JSON)

            except Exception:
                error(" Function: %s\nSender: %s\nMessage: %s\nError: %s" % (
                        target, self.getSender(), message,
                        traceback.format_exc()))
                return
        else:
            error("No Target: %s message: %s sender: %s" % (target, message,
                                                           self.getSender()))
            return

    def closed(self, code, reason="Client disconnected witout reason."):
        if self in WebSocketRouter.usermap:
            del WebSocketRouter.usermap[self]
        elif self in WebSocketRouter.nodemap:
            del WebSocketRouter.nodemap[self]
        else:
            error(" Untracked client disconnected: %s" % reason)

        # stop all nodes if there are no users
        if len(WebSocketRouter.usermap) == 0:
            for nodename in WebSocketRouter.nodemap:
                if type(nodename) is str:
                    WebSocketRouter.nodemanager.stop(nodename)

class NodeManager():

    def __init__(self):
        WebSocketRouter.register('nodemanager', NodeManager.handler)

    @staticmethod
    def handler(websocket, message):
        # message is name of node to start

        cmdfile = os.path.join(NODE_DIR, '%s.py' % message)
        pidfile = os.path.join(NODE_DIR, '%s.pid' % message)

        debug(cmdfile)
        debug(pidfile)

        if os.path.exists(pidfile):
            debug("pid file exists, check if it's running")
            file = open(pidfile)
            try:
                pid = int(file.read())
            except:
                debug("%s.pid does not contain a valid process id" % nodename)
            else:
                if NodeManager.check_pid(pid):
                    debug("process is still running")
                    return message

        pid = Popen(["python", cmdfile]).pid

        debug("PID: %s" % str(pid))

        _file = open(pidfile, 'w')
        _file.write(str(pid))
        _file.flush()
        _file.close()

        return None

    @staticmethod
    def check_pid(pid):
        """ Check For the existence of a unix pid. """
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    def stop(self, nodename):

        pidfile = os.path.join(NODE_DIR, '%s.pid' % nodename)
        if os.path.exists(pidfile):
            try:
                exitCode = str(os.kill(pid, signal.SIGKILL))
                debug("Exit code: %s" % exitCode)
            except:
                debug("unable to kill %s process" % nodename)
            finally:
                os.remove(pidfile)
        return nodename

        # cherrypy.engine.publish('websocket-broadcast', TextMessage(reason))

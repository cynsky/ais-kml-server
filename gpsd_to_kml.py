#!/usr/bin/env python

from twisted.internet import reactor, protocol, task
from twisted.internet.serialport import SerialPort
from twisted.protocols import basic
import math
from twisted.internet.protocol import Protocol, ReconnectingClientFactory
import json
import datetime
import calendar
import time

class GpsdClient(Protocol):
    def __init__(self):
	self.gga = {}
        self.gga['msg_count'] = 0
	self.rmc = {}
        self.rmc['msg_count'] = 0
	self.lat = 0
	self.lon = 0
	self.alt = 0
	self.velocity = 0
	self.heading = 0
	self.timestamp = 0
        self.targets = {}

    def connectionMade(self):
	self.transport.write('?WATCH={"json":true,"enable":true}\r\n')

    def dataReceived(self, data):
	lines = data.split("\r\n")
	for line in lines:
	    try:
		msg = json.loads(line)
	    except ValueError:
		continue
            if 'mmsi' not in msg:
                continue
            if 'lat' not in msg:
                continue
            if 'lon' not in msg:
                continue

            _id = msg['mmsi']
            lat = msg['lat'] / 600000.0
            lon = msg['lon'] / 600000.0
            ts = time.time()
            print ts, _id, lat, lon

            self.targets[_id] = (ts, lat, lon, 0)

    def get_targets(self):
        return self.targets

    def cull(self):
        """
        Periodically this should be called to dump targets which haven't been
        heard from in a while.
        """
        delete_icaos = []
        for icao, met in self.targets.iteritems():
            print met[0]
            #if (calendar.timegm(datetime.utcnow().utctimetuple()) - met[0]) > 120:
            if (time.time() - met[0]) > 120:
                delete_icaos.append(icao)

        for i in delete_icaos:
            print "deleting", i
            del self.targets[i]


class GpsdClientFactory(ReconnectingClientFactory):
    def __init__(self):
        self.client = None
        self.connected = False

    def startedConnecting(self, connector):
        print 'Started to connect.'

    def buildProtocol(self, addr):
        print 'Connected.'
        print 'Resetting reconnection delay'
        self.connected = True
        self.resetDelay()
        self.client = GpsdClient()
        return self.client

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason
        self.client = None
        self.connected = False
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason
        self.client = None
        self.connected = False
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def is_connected(self):
        return self.connected

    def get_client(self):
        return self.client

from twisted.web import server, resource
from lxml import etree
from pykml.factory import KML_ElementMaker as KML

class Simple(resource.Resource):

    def __init__(self, _factory):
        self.factory = _factory

    isLeaf = True
    def render_GET(self, request):
        if not self.factory.is_connected():
            return

        request.responseHeaders.setRawHeaders("content-type", ['application/vnd.google-earth.kml+xml'])

        doc = KML.kml()
        folder = KML.Folder(KML.name("planes"))
        doc.append(folder)
        targ = self.factory.get_client().get_targets()
        for icao, met in targ.iteritems():
            folder.append(
                KML.Placemark(
                    KML.name('%x' % icao),
                    KML.Point(
                        KML.extrude(True),
                        KML.altitudeMode('relativeToGround'),
                        KML.coordinates('%f,%f,%f' % (met[2], met[1], met[3])),
                    ),
                ),
            )
        return etree.tostring(etree.ElementTree(doc),pretty_print=True)

factory = GpsdClientFactory()
reactor.connectTCP('localhost', 2947, factory)

site = server.Site(Simple(factory))
reactor.listenTCP(8081, site)

reactor.run()

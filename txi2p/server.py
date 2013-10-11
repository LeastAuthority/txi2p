# Copyright (c) str4d <str4d@mail.i2p>
# See COPYING for details.

from twisted.internet.defer import Deferred
from twisted.internet.protocol import Factory

from txi2p.protocol import I2PServerTunnelCreatorBOBClient


class BOBI2PServerFactory(Factory):
    protocol = I2PServerTunnelCreatorBOBClient
    bobProto = None
    canceled = False

    def _cancel(self, d):
        self.bobProto.sender.transport.abortConnection()
        self.canceled = True

    def __init__(self, serverFactory, bobEndpoint, keypairPath):
        self.serverFactory = serverFactory
        self.bobEndpoint = bobEndpoint
        self.keypairPath = keypairPath
        self.deferred = Deferred(self._cancel)

    def startFactory(self):
        try:
            keypairFile = open(self.keypairPath, 'r')
            self.keypair = keypairFile.read()
            keypairFile.close()
        except IOError:
            self.keypair = None

    def buildProtocol(self, addr):
        proto = self.protocol()
        proto.factory = self
        self.bobProto = proto
        return proto

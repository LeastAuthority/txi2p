# Copyright (c) str4d <str4d@mail.i2p>
# See COPYING for details.

from twisted.internet.defer import Deferred
from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint
from twisted.internet.protocol import ClientFactory, Factory

from txi2p.bob.protocol import (I2PClientTunnelCreatorBOBClient,
                                I2PServerTunnelCreatorBOBClient,
                                I2PTunnelRemoverBOBClient,
                                I2PClientTunnelProtocol,
                                I2PServerTunnelProtocol)


class BOBI2PClientFactory(ClientFactory):
    protocol = I2PClientTunnelCreatorBOBClient
    bobProto = None
    canceled = False
    removeTunnelWhenFinished = True

    def _cancel(self, d):
        self.bobProto.sender.transport.abortConnection()
        self.canceled = True

    def __init__(self, reactor, clientFactory, bobEndpoint, dest, tunnelNick=None):
        self._reactor = reactor
        self._clientFactory = clientFactory
        self._bobEndpoint = bobEndpoint
        self.dest = dest
        self.tunnelNick = tunnelNick
        self.deferred = Deferred(self._cancel);

    def buildProtocol(self, addr):
        proto = self.protocol()
        proto.factory = self
        self.bobProto = proto
        return proto

    def bobConnectionFailed(self, reason):
        if not self.canceled:
            self.deferred.errback(reason)

    # This method is not called if an endpoint deferred errbacks
    def clientConnectionFailed(self, connector, reason):
        self.bobConnectionFailed(reason)

    def i2pTunnelCreated(self):
        # BOB is now listening for a tunnel.
        # BOB only listens on TCP4 (for now).
        clientEndpoint = TCP4ClientEndpoint(self._reactor, self.inhost, self.inport)
        # Wrap the client Factory.
        wrappedFactory = BOBClientFactoryWrapper(self._clientFactory,
                                                 self._bobEndpoint,
                                                 self.tunnelNick,
                                                 self.removeTunnelWhenFinished)
        wrappedFactory.setDest(self.dest)
        d = clientEndpoint.connect(wrappedFactory)
        def checkProto(proto):
            if proto is None:
                self.deferred.cancel()
            return proto
        d.addCallback(checkProto)
        # When the Deferred returns an IProtocol, pass it on.
        d.chainDeferred(self.deferred)


class BOBI2PServerFactory(Factory):
    protocol = I2PServerTunnelCreatorBOBClient
    bobProto = None
    canceled = False
    removeTunnelWhenFinished = True

    def _cancel(self, d):
        self.bobProto.sender.transport.abortConnection()
        self.canceled = True

    def __init__(self, reactor, serverFactory, bobEndpoint, keypairPath, tunnelNick=None):
        self._reactor = reactor
        self._serverFactory = serverFactory
        self._bobEndpoint = bobEndpoint
        self.keypairPath = keypairPath
        self.tunnelNick = tunnelNick
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

    def bobConnectionFailed(self, reason):
        if not self.canceled:
            self.deferred.errback(reason)

    # This method is not called if an endpoint deferred errbacks
    def clientConnectionFailed(self, connector, reason):
        self.bobConnectionFailed(reason)

    def i2pTunnelCreated(self):
        # BOB will now forward data to a listener.
        # BOB only forwards to TCP4 (for now).
        serverEndpoint = TCP4ServerEndpoint(self._reactor, self.outport)
        # Wrap the server Factory.
        wrappedFactory = BOBServerFactoryWrapper(self._serverFactory,
                                                 self._bobEndpoint,
                                                 self.tunnelNick,
                                                 self.removeTunnelWhenFinished)
        d = serverEndpoint.listen(wrappedFactory)
        def checkProto(proto):
            if proto is None:
                self.deferred.cancel()
            return proto
        d.addCallback(checkProto)
        # When the Deferred returns an IListeningPort, pass it on.
        d.chainDeferred(self.deferred)


class BOBI2PTunnelRemoverFactory(ClientFactory):
    protocol = I2PTunnelRemoverBOBClient

    def __init__(self, tunnelNick):
        self.tunnelNick = tunnelNick


class BOBFactoryWrapperCommon(object):
    def __init__(self, wrappedFactory,
                       bobEndpoint,
                       tunnelNick,
                       removeTunnelWhenFinished):
        self.w = wrappedFactory
        self.bobEndpoint = bobEndpoint
        self.tunnelNick = tunnelNick
        self.removeTunnelWhenFinished = removeTunnelWhenFinished

    def __getattr__(self, attr):
        return getattr(self.w, attr)

    def stopFactory():
        self.w.stopFactory()
        if self.removeTunnelWhenFinished:
            rmTunnelFac = BOBI2PTunnelRemoverFactory(self.tunnelNick)
            self.bobEndpoint.connect(rmTunnelFac)


class BOBClientFactoryWrapper(BOBFactoryWrapperCommon):
    protocol = I2PClientTunnelProtocol

    def setDest(self, dest):
        self.dest = dest

    def buildProtocol(self, addr):
        wrappedProto = self.w.buildProtocol(addr)
        proto = self.protocol(wrappedProto, self.dest)
        proto.factory = self
        self.bobProto = proto
        return proto


class BOBServerFactoryWrapper(BOBFactoryWrapperCommon):
    protocol = I2PServerTunnelProtocol

    def buildProtocol(self, addr):
        wrappedProto = self.w.buildProtocol(addr)
        proto = self.protocol(wrappedProto)
        proto.factory = self
        self.bobProto = proto
        return proto

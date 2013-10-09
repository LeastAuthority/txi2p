# Copyright (c) str4d <str4d@mail.i2p>
# See COPYING for details.

from parsley import makeProtocol
from twisted.internet import defer, interfaces, protocol
from zope.interface import implementer

from txi2p import grammar


class BOBSender(object):
    def __init__(self, transport):
        self.transport = transport


class BOBReceiver(object):
    def __init(self, sender):
        self.sender = sender


# A Protocol for making an I2P client tunnel via BOB
I2PClientTunnelCreatorBOBClient = makeProtocol(
    grammar.i2pClientTunnelCreatorBOBGrammarSource,
    I2PClientTunnelCreatorBOBSender,
    I2PClientTunnelCreatorBOBReceiver)

# A Protocol for making an I2P server tunnel via BOB
I2PServerTunnelCreatorBOBClient = makeProtocol(
    grammar.i2pServerTunnelCreatorBOBGrammarSource,
    I2PServerTunnelCreatorBOBSender,
    I2PServerTunnelCreatorBOBReceiver)


class I2PClientFactory(protocol.ClientFactory):
    currentCandidate = None
    canceled = False

    def _cancel(self, d):
        self.currentCandidate.sender.transport.abortConnection()
        self.canceled = True

    def __init__(self, dest, providedFactory):
        self.dest = dest
        self.providedFactory = providedFactory
        self.deferred = defer.Deferred(self._cancel);

    def buildProtocol(self, addr):
        proto = None # TODO: Make protocol!
        proto.factory = self
        self.currentCandidate = proto
        return proto

    def i2pConnectionFailed(self, reason):
        if not self.canceled:
            self.deferred.errback(reason)

    # This method is not called if an endpoint deferred errbacks
    def clientConnectionFailed(self, connector, reason):
        self.i2pConnectionFailed(reason)

    def i2pConnectionEstablished(self, i2pProtocol):
        # We have a connection! Use it.
        proto = self.providedFactory.buildProtocol(
            i2pProtocol.sender.transport.getPeer()) # TODO: Understand this - need to use the new tunnel, not BOB.
        if proto is None:
            self.deferred.cancel()
            return
        i2pProtocol.i2pEstablished(proto)
        self.deferred.callback(proto)

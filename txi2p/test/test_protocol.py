# Copyright (c) str4d <str4d@mail.i2p>
# See COPYING for details.

from twisted.test import proto_helpers
from twisted.trial import unittest

from txi2p.protocol import I2PClientTunnelCreatorBOBClient
from txi2p.test.util import FakeBOBI2PClientFactory


class TestI2PClientTunnelCreatorBOBClient(unittest.TestCase):
    def makeProto(self, *a, **kw):
        protoClass = kw.pop('_protoClass', I2PClientTunnelCreatorBOBClient)
        fac = FakeBOBI2PClientFactory(*a, **kw)
        fac.protocol = protoClass
        proto = fac.buildProtocol(None)
        transport = proto_helpers.StringTransport()
        transport.abortConnection = lambda: None
        proto.makeConnection(transport)
        return fac, proto

    def test_initBOB(self):
        fac, proto = self.makeProto()
        fac.tunnelNick = 'spam'
        proto.dataReceived('BOB 00.00.10\nOK\n')
        self.assertEqual(proto.transport.value(), 'setnick spam\n')

    def test_nickSetWithKeypair(self):
        fac, proto = self.makeProto()
        fac.tunnelNick = 'spam'
        fac.keypair = 'eggs'
        proto.dataReceived('BOB 00.00.10\nOK\n')
        proto.transport.clear()
        proto.dataReceived('OK HTTP 418\n')
        self.assertEqual(proto.transport.value(), 'setkeys eggs\n')

    def test_destFetchedAfterNickSetWithKeypair(self):
        fac, proto = self.makeProto()
        fac.tunnelNick = 'spam'
        fac.keypair = 'eggs'
        proto.dataReceived('BOB 00.00.10\nOK\n')
        proto.transport.clear()
        proto.dataReceived('OK HTTP 418\n')
        proto.transport.clear()
        proto.dataReceived('OK HTTP 418\n')
        self.assertEqual(proto.transport.value(), 'getdest\n')

    def test_nickSetWithNoKeypair(self):
        fac, proto = self.makeProto()
        fac.tunnelNick = 'spam'
        proto.dataReceived('BOB 00.00.10\nOK\n')
        proto.transport.clear()
        proto.dataReceived('OK HTTP 418\n')
        self.assertEqual(proto.transport.value(), 'newkeys\n')

    def test_keypairFetchedAfterNickSetWithNoKeypair(self):
        fac, proto = self.makeProto()
        fac.tunnelNick = 'spam'
        proto.dataReceived('BOB 00.00.10\nOK\n')
        proto.transport.clear()
        proto.dataReceived('OK HTTP 418\n')
        proto.transport.clear()
        proto.dataReceived('OK shrubbery\n') # The new Destination
        self.assertEqual(proto.transport.value(), 'getkeys\n')

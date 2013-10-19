# Copyright (c) str4d <str4d@mail.i2p>
# See COPYING for details.

from parsley import makeProtocol
from twisted.internet.protocol import Protocol

from txi2p import grammar

DEFAULT_INPORT  = 9000
DEFAULT_OUTPORT = 9001


class BOBSender(object):
    def __init__(self, transport):
        self.transport = transport

    def sendClear(self):
        self.transport.write('clear\n')

    def sendGetdest(self):
        self.transport.write('getdest\n')

    def sendGetkeys(self):
        self.transport.write('getkeys\n')

    def sendGetnick(self, tunnelNick):
        self.transport.write('getnick %s\n' % tunnelNick)

    def sendInhost(self, inhost):
        self.transport.write('inhost %s\n' % inhost)

    def sendInport(self, inport):
        self.transport.write('inport %s\n' % inport)

    def sendList(self):
        self.transport.write('list\n')

    def sendNewkeys(self):
        self.transport.write('newkeys\n')

    def sendOption(self):
        self.transport.write('option\n')

    def sendOuthost(self, outhost):
        self.transport.write('outhost %s\n' % outhost)

    def sendOutport(self, outport):
        self.transport.write('outport %s\n' % outport)

    def sendQuiet(self):
        self.transport.write('quiet\n')

    def sendQuit(self):
        self.transport.write('quit\n')

    def sendSetkeys(self, keys):
        self.transport.write('setkeys %s\n' % keys)

    def sendSetnick(self, tunnelNick):
        self.transport.write('setnick %s\n' % tunnelNick)

    def sendShow(self):
        self.transport.write('show\n')

    def sendShowprops(self):
        self.transport.write('showprops\n')

    def sendStart(self):
        self.transport.write('start\n')

    def sendStatus(self, tunnelNick):
        self.transport.write('status %s\n' % tunnelNick)

    def sendStop(self):
        self.transport.write('stop\n')

    def sendVerify(self, key):
        self.transport.write('verify %s\n' % key)

    def sendVisit(self):
        self.transport.write('visit\n')


class BOBReceiver(object):
    currentRule = 'State_init'

    def __init__(self, sender):
        self.sender = sender
        self.tunnelExists = False

    def prepareParsing(self, parser):
        # Store the factory for later use
        self.factory = parser.factory

    def finishParsing(self, reason):
        self.factory.bobConnectionFailed(reason)

    def initBOB(self, version):
        self.sender.sendList()
        self.currentRule = 'State_list'

    def processTunnelList(self, tunnels):
        # Default port offset is at the end of the tunnels list
        offset = 2*(len(tunnels))
        for i in range(0, len(tunnels)):
            if tunnels[i]['nickname'] == self.factory.tunnelNick:
                self.tunnelExists = True
                self.tunnelRunning = tunnels[i]['running']
                offset = 2*i
                # The tunnel will be removed by the Factory
                # that created it.
                self.factory.removeTunnelWhenFinished = False
                break
        # If the in/outport were not user-configured, set them.
        if not hasattr(self.factory, 'inport'):
            self.factory.inport = DEFAULT_INPORT + offset
        if not hasattr(self.factory, 'outport'):
            self.factory.outport = DEFAULT_OUTPORT + offset

    def setnick(self, success, info):
        if success:
            if hasattr(self.factory, 'keypair'): # If a keypair was provided, use it
                self.sender.sendSetkeys(self.factory.keypair)
                self.currentRule = 'State_setkeys'
            else: # Get a new keypair
                self.sender.sendNewkeys()
                self.currentRule = 'State_newkeys'

    def setkeys(self, success, info):
        if success:
            # Update the local Destination
            self.sender.sendGetdest()
            self.currentRule = 'State_getdest'

    def newkeys(self, success, info):
        if success:
            # Save the new local Destination
            self.factory.localDest = info
            # Get the new keypair
            self.sender.sendGetkeys()
            self.currentRule = 'State_getkeys'


class I2PClientTunnelCreatorBOBReceiver(BOBReceiver):
    def list(self, success, info, data):
        if success:
            if hasattr(self.factory, 'tunnelNick'):
                self.processTunnelList(data)
                if self.tunnelExists:
                    self.sender.sendGetnick(self.factory.tunnelNick)
                    self.currentRule = 'State_getnick'
                else:
                    # Set tunnel nickname (and update keypair/localDest state)
                    self.sender.sendSetnick(self.factory.tunnelNick)
                    self.currentRule = 'State_setnick'
            else:
                print 'Factory has no tunnelNick'

    def getnick(self, success, info):
        if success:
            if self.tunnelRunning:
                self.sender.sendStop()
                self.currentRule = 'State_stop'
            else:
                # Update the local Destination
                self.sender.sendGetdest()
                self.currentRule = 'State_getdest'

    def stop(self, success, info):
        if success:
            # Update the local Destination
            self.sender.sendGetdest()
            self.currentRule = 'State_getdest'

    def getdest(self, success, info):
        if success:
            # Save the local Destination
            self.factory.localDest = info
            if self.tunnelExists:
                # Get the keypair
                self.sender.sendGetkeys()
                self.currentRule = 'State_getkeys'
            else:
                self._setInhost()

    def getkeys(self, success, info):
        if success:
            # Save the keypair
            self.factory.keypair = info
            self._setInhost()

    def _setInhost(self):
        if hasattr(self.factory, 'inhost'):
            self.sender.sendInhost(self.factory.inhost)
            self.currentRule = 'State_inhost'
        else:
            print 'Factory has no inhost'

    def inhost(self, success, info):
        if success:
            if hasattr(self.factory, 'inport'):
                self.sender.sendInport(self.factory.inport)
                self.currentRule = 'State_inport'
            else:
                print 'Factory has no inport'

    def inport(self, success, info):
        if success:
            self.sender.sendStart()
            self.currentRule = 'State_start'

    def start(self, success, info):
        if success:
            print "Client tunnel started"
            self.factory.i2pTunnelCreated()


class I2PServerTunnelCreatorBOBReceiver(BOBReceiver):
    def list(self, success, info, data):
        if success:
            if hasattr(self.factory, 'tunnelNick'):
                self.processTunnelList(data)
                if self.tunnelExists:
                    self.sender.sendGetnick(self.factory.tunnelNick)
                    self.currentRule = 'State_getnick'
                else:
                    # Set tunnel nickname (and update keypair/localDest state)
                    self.sender.sendSetnick(self.factory.tunnelNick)
                    self.currentRule = 'State_setnick'
            else:
                print 'Factory has no tunnelNick'

    def getnick(self, success, info):
        if success:
            if self.tunnelRunning:
                self.sender.sendStop()
                self.currentRule = 'State_stop'
            else:
                # Update the local Destination
                self.sender.sendGetdest()
                self.currentRule = 'State_getdest'

    def stop(self, success, info):
        if success:
            # Update the local Destination
            self.sender.sendGetdest()
            self.currentRule = 'State_getdest'

    def getdest(self, success, info):
        if success:
            # Save the local Destination
            self.factory.localDest = info
            self._setOuthost()

    def getkeys(self, success, info):
        if success:
            # Save the keypair
            self.factory.keypair = info
            self._setOuthost()

    def _setOuthost(self):
        if hasattr(self.factory, 'outhost'):
            self.sender.sendOuthost(self.factory.outhost)
            self.currentRule = 'State_outhost'
        else:
            print 'Factory has no outhost'

    def outhost(self, success, info):
        if success:
            if hasattr(self.factory, 'outport'):
                self.sender.sendOutport(self.factory.outport)
                self.currentRule = 'State_outport'
            else:
                print 'Factory has no outport'

    def outport(self, success, info):
        if success:
            self.sender.sendStart()
            self.currentRule = 'State_start'

    def start(self, success, info):
        if success:
            print "Server tunnel started"
            self.factory.i2pTunnelCreated()

class I2PTunnelRemoverBOBReceiver(BOBReceiver):
    def list(self, success, info, data):
        if success:
            if hasattr(self.factory, 'tunnelNick'):
                self.processTunnelList(data)
                if self.tunnelExists:
                    # Get tunnel for nickname
                    self.sender.sendGetnick(self.factory.tunnelNick)
                    self.currentRule = 'State_getnick'
                else:
                    # Tunnel already removed
                    pass
            else:
                print 'Factory has no tunnelNick'

    def getnick(self, success, info):
        if success:
            self.sender.sendStop()
            self.currentRule = 'State_stop'

    def stop(self, success, info):
        if success:
            self.sender.sendClear()
            self.currentRule = 'State_clear'

    def clear(self, success, info):
        if success:
            print 'Tunnel removed'
        else: # Try again. TODO: Limit retries
            self.sender.sendClear()


# A Protocol for making an I2P client tunnel via BOB
I2PClientTunnelCreatorBOBClient = makeProtocol(
    grammar.bobGrammarSource,
    BOBSender,
    I2PClientTunnelCreatorBOBReceiver)

# A Protocol for making an I2P server tunnel via BOB
I2PServerTunnelCreatorBOBClient = makeProtocol(
    grammar.bobGrammarSource,
    BOBSender,
    I2PServerTunnelCreatorBOBReceiver)

# A Protocol for removing a BOB I2P tunnel
I2PTunnelRemoverBOBClient = makeProtocol(
    grammar.bobGrammarSource,
    BOBSender,
    I2PTunnelRemoverBOBReceiver)


class I2PClientTunnelProtocol(Protocol):
    def __init__(self, wrappedProto, dest):
        self.wrappedProto = wrappedProto
        self.dest = dest

    def connectionMade(self):
        # First line sent must be the Destination to connect to.
        self.transport.write(self.dest + '\n')

    def dataReceived(self, data):
        # Pass all received data to the wrapped Protocol.
        self.wrappedProto.dataReceived(data)


class I2PServerTunnelProtocol(Protocol):
    def __init__(self, wrappedProto):
        self.wrappedProto = wrappedProto
        self.peer = None

    def dataReceived(self, data):
        if self.peer:
            # Pass all other data to the wrapped Protocol.
            self.wrappedProto.dataReceived(data)
        else:
            # First line is the peer's Destination.
            # TODO: Return this to the user somehow.
            self.peer = data.split('\n')[0]

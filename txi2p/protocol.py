# Copyright (c) str4d <str4d@mail.i2p>
# See COPYING for details.

from parsley import makeProtocol

from txi2p import grammar


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
        self.transport.write('\n')

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

    def prepareParsing(self, parser):
        # Store the factory for later use
        self.factory = parser.factory

    def finishParsing(self, reason):
        print reason

    def initBOB(self, version):
        """Override this to start protocol logic"""
        pass

    def clear(self, success, info):
        if not success: # Try again. TODO: Limit retries
            print info
            self.sender.sendClear()

    def getdest(self, success, info):
        if success:
            # Save the local Destination
            self.factory.localDest = info
        else:
            print info

    def getkeys(self, success, info):
        if success:
            # Save the keypair
            self.factory.keypair = info
        else:
            print info

    def getnick(self, success, info):
        if not success:
            print info

    def inhost(self, success, info):
        if not success:
            print info

    def inport(self, success, info):
        if not success:
            print info

    def list(self, success, info, data):
        if not success:
            print info

    def newkeys(self, success, info):
        if success:
            # Save the new local Destination
            self.factory.localDest = info
            # Get the new keypair
            self.sender.sendGetkeys()
            self.currentRule = 'State_getkeys'
        else:
            print info

    def option(self, success, info):
        if not success:
            print info

    def outhost(self, success, info):
        if not success:
            print info

    def outport(self, success, info):
        if not success:
            print info

    def quiet(self, success, info):
        if not success:
            print info

    def quit(self, success, info):
        pass

    def setkeys(self, success, info):
        if success:
            # Update the local Destination
            self.sender.sendGetdest()
            self.currentRule = 'State_getdest'
        else:
            print info

    def setnick(self, success, info):
        if success:
            if hasattr(self.factory, 'keypair'): # If a keypair was provided, use it
                self.sender.sendSetkeys(self.factory.keypair)
                self.currentRule = 'State_setkeys'
            else: # Get a new keypair
                self.sender.sendNewkeys()
                self.currentRule = 'State_newkeys'
        else:
            print info

    def show(self, success, info):
        if not success:
            print info

    def showprops(self, success, info):
        if not success:
            print info

    def start(self, success, info):
        if not success:
            print info

    def status(self, success, info):
        if not success:
            print info

    def stop(self, success, info):
        if not success:
            print info

    def verify(self, success, info):
        if not success:
            print info

    def visit(self, success, info):
        pass


class I2PClientTunnelCreatorBOBReceiver(BOBReceiver):
    def initBOB(self, version):
        if hasattr(self.factory, 'tunnelNick'):
            # Set tunnel nickname (and update keypair/localDest state)
            self.sender.sendSetnick(self.factory.tunnelNick)
            self.currentRule = 'State_setnick'
        else:
            print 'Factory has no tunnelNick'

    def getdest(self, success, info):
        super.getdest(success, info)
        if success:
            self._setInhost()

    def getkeys(self, success, info):
        super.getkeys(success, info)
        if success:
            self._setInhost()

    def _setInhost():
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
    def initBOB(self, version):
        if hasattr(self.factory, 'tunnelNick'):
            # Set tunnel nickname (and update keypair/localDest state)
            self.sender.sendSetnick(self.factory.tunnelNick)
            self.currentRule = 'State_setnick'
        else:
            print 'Factory has no tunnelNick'

    def getdest(self, success, info):
        super.getdest(success, info)
        if success:
            self._setOuthost()

    def getkeys(self, success, info):
        super.getkeys(success, info)
        if success:
            self._setOuthost()

    def _setOuthost():
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
    def initBOB(self, version):
        if hasattr(self.factory, 'tunnelNick'):
            # Get tunnel for nickname
            self.sender.sendGetnick(self.factory.tunnelNick)
            self.currentRule = 'State_setnick'
        else:
            print 'Factory has no tunnelNick'

    def getnick(self, success, info):
        super.getnick(success, info)
        if success:
            self.sender.sendStop()
            self.currentRule = 'State_stop'

    def stop(self, success, info):
        super.stop(success, info)
        if success:
            self.sender.sendClear()
            self.currentRule = 'State_clear'

    def clear(self, success, info):
        super.stop(success, info)
        if success:
            print 'Tunnel removed'


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

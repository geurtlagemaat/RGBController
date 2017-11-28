from bliknetlib import nodeControl

__author__ = 'geurt'

import datetime
from twisted.internet import reactor
from serialNodesController import SerialNodesController


if __name__ == '__main__':
    now = datetime.datetime.now()
    oNodeControl = nodeControl.nodeControl(r'settings/bliknetnode.conf')
    oNodeControl.log.info("BliknetNode: %s starting at: %s." % (oNodeControl.nodeID, now))

    mySerialNodesController = SerialNodesController(oNodeControl)

    if oNodeControl.nodeProps.has_option('watchdog', 'circusWatchDog'):
        if oNodeControl.nodeProps.getboolean('watchdog', 'circusWatchDog') == True:
            oNodeControl.circusNotifier.start()

    reactor.run()
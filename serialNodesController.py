import traceback
from time import sleep
import datetime
from bliknetlib.serialNodesProtocol import SerialNodesProtocol
from twisted.internet.serialport import SerialPort
from twisted.internet import reactor, task
import serial
import RGBColors
from bliknetlib import astro_functions

ARMED = False

class SerialNodesController(object):
    def __init__(self, oNodeControl):
        self._NodeControl = oNodeControl
        self._AfterPIREvent = None
        self._ResetState = 10

        # list all serial ports: python -m serial.tools.list_ports
        self._connectSerialPort()
        l = task.LoopingCall(self.eCheckLights)
        l.start(300)

    def _connectSerialPort(self):
        self.Close()
        myProtocol = SerialNodesProtocol(self._NodeControl, OnReceive=self.OnMsgReceive)
        self._serialPort = SerialPort(myProtocol, self._NodeControl.nodeProps.get('serialnodes', 'serialport'),
                                      reactor,
                                      baudrate=9600,
                                      bytesize=serial.EIGHTBITS,
                                      parity=serial.PARITY_NONE)
        sleep(1)

    def eCheckLights(self):
        if self._AfterPIREvent is None:
            self.setNormalState()

    def OnMsgReceive(self, RecMsg):
        myNodeID = '112' # self._NodeControl.nodeProps.get('system', 'nodeId')
        if str(RecMsg.ToAdress) == myNodeID:
            # for this node
            if int(RecMsg.Function)==1:
                # PIR alert
                if self._AfterPIREvent is None:
                    self._NodeControl.MQTTPublish(sTopic="overloop/pirevent", sValue="ON",
                                                  iQOS=0,
                                                  bRetain=False)
                    reactor.callLater(self._ResetState, self.ResetState, topic="overloop/pirevent")
                    if ARMED:
                        RGBColors.sendEffectScheme(self, self._NodeControl, 752, RGBColors.EFFECT_ALERT)
                    elif astro_functions.isDusk(self._NodeControl):
                        RGBColors.sendEffectScheme(self, self._NodeControl, 752, RGBColors.EFFECT_SILENT_NIGHT_WAVE)
                    else:
                        RGBColors.sendRGBValue(self, self._NodeControl, 752, RGBColors.FRIENDLYHELLO)
                    self._AfterPIREvent = reactor.callLater(10, self.afterPIREvent)

    def afterPIREvent(self):
        reactor.callFromThread(self.switchToNoneAlertState)

    def ResetState(self, topic):
        self._NodeControl.MQTTPublish(sTopic=topic, sValue="OFF", iQOS=0, bRetain=False)

    def switchToNoneAlertState(self):
        self._AfterPIREvent = None
        self._connectSerialPort()
        self.setNormalState()

    def setNormalState(self):
        if astro_functions.isDusk(self._NodeControl):
            self._NodeControl.log.debug('Dusk: setting quit nights lights')
            RGBColors.sendColorScheme(self, self._NodeControl, 752, RGBColors.COLORSCHEME_QUITNIGHT_01)
        else:
            self._NodeControl.log.debug('Daytime: switch lights off')
            RGBColors.sendRGBValue(self, self._NodeControl, 752, RGBColors.ALLOFF)

    def SendMessage(self, sSerialMessage):
        try:
            self._serialPort.write(sSerialMessage)
            sleep(0.1)
            return True
        except Exception, exp:
            print traceback.format_exc()
            self._NodeControl.log.error("SendMessage error: %s." % traceback.format_exc())
            return False

    def Close(self):
        try:
            self._serialPort.loseConnection()
            self._serialPort = None
        except:
            pass
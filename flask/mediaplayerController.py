from subprocess import Popen
import logging

logging.basicConfig(level=logging.DEBUG)

class MediaplayerController():
    def __init__(self):
        self.fifoName = '/home/pi/mediaplayer/fifo'
        self.process = None
        self.fifo = None
        self.url = None
        self.cmd = None

    def _open(self, url):
        self.url = url
        if not self.process:
            # -idle will allow no url
            # self.cmd = 'mplayer -quiet -noconsolecontrols -slave -input file={0} {1}'.format(self.fifoName, url)
            self.cmd = 'mplayer -quiet -noconsolecontrols -slave -input file={0} -idle'.format(self.fifoName)
            with open('/dev/null') as DEVNULL:
                self.process = Popen(args = self.cmd, shell = True, stdin=DEVNULL, close_fds=True)
            self.fifo = open(self.fifoName, 'a')
        #else:
            #self._message("loadfile " + url)
        self._message("loadfile " + url)

    def _message(self, msg):
        self.fifo.write(msg)
        self.fifo.write("\n")
        self.fifo.flush()

    def play(self, url):
        logging.debug("MPC: playing " + url)
        self._open(url)

    def write(self, message):
        if self.process:
            self._message(message)

    def close(self):
        if self.process:
            self._message('quit')
            self.process = None
            self.fifo = None
            self.url = None
            self.cmd = None
            

MEDIAPLAYER = None
def get_mediaplayer():
    global MEDIAPLAYER
    if not MEDIAPLAYER:
        MEDIAPLAYER = MediaplayerController()
    return MEDIAPLAYER

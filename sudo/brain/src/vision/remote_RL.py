import time
import logging
import termios, sys, os
import threading

### Import local dependencies
import configparse
import util.nullhandler
import util.loggingextra as loggingextra
from util.ticker import Ticker
from abstractvisionmodule import AbstractVisionModule as avm

logging.getLogger('Borg.Brain.Vision.Remote').addHandler(util.nullhandler.NullHandler())

TERMIOS = termios
def getkey():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] = new[3] & ~TERMIOS.ICANON & ~TERMIOS.ECHO
    new[6][TERMIOS.VMIN] = 0
    new[6][TERMIOS.VTIME] = 1

    termios.tcsetattr(fd, TERMIOS.TCSANOW, new)
    c = None
    try:
        c = os.read(fd, 1)
    finally:
        termios.tcsetattr(fd, TERMIOS.TCSAFLUSH, old)
    return c
     

class Remote(avm):
    """
    Remote control the pioneer / scanner
    """
    def __init__(self,
                 controller_ip,
                 controller_port,
                 update_frequency=5):
        """
        Constructor
        """
        self.logger = logging.getLogger("Borg.Brain.Vision.Remote")
        super(Remote, self).__init__(controller_ip, controller_port)

        # Store configuration
        self.__ticker = Ticker(frequency=update_frequency)
        self.last_odo = None

        self.file_lock = threading.Lock()
        self.process = None
        self.__last_print = 0 

    def __del__(self):
        self.stop()

    def stop(self):
        """
        When stopping the module, make sure the PCD Writer and
        SLAM6D handlers also stop
        """
        self.disconnect()

    def train(self):
        pass

    def run(self):
        """start loop which gets a new image, then processes it"""
        while self.is_connected():
            self.__ticker.tick() # Tick (sleep)

            if self.process and self.process.is_alive():
                self.update()
                continue

            c = getkey() 
            if c:
                if c == 'w':
                    print "Moving forward"
                    self.add_property("name", "pioneer_command")
                    self.add_property("pioneer_command", "mmove")
                elif c == 'a':
                    print "Turning left"
                    self.add_property("name", "pioneer_command")
                    self.add_property("pioneer_command", "mleft")
                elif c == 'd':
                    print "Turning right"
                    self.add_property("name", "pioneer_command")
                    self.add_property("pioneer_command", "mright")
                elif c == 'f':
                    self.add_property("name", "pioneer_command")
                    self.add_property("pioneer_command", "finish")
                elif c == 'p':
                    self.add_property("name", "remote_command")
                    self.add_property("pioneer_command", "record")
                elif c == 'h':
                    print "[w] = forward    [a] = left         [d] = right              [f] = finish"

            
            ############################
            # Send data
            self.update()

    def handle_custom_commands(self, entry):
        if entry['command'] == "odometry":
            odo = entry['params'][1]
            if odo != self.last_odo:
                if self.__last_print < time.time() - 2:
                    print "Current position: %s" % repr(odo)
                    self.__last_print = time.time()
                self.last_odo = odo


if __name__ == "__main__":
    logging.getLogger('Borg.Brain').addHandler(loggingextra.ScreenOutput())
    logging.getLogger('Borg.Brain').setLevel(logging.INFO)

    #PARSE COMMAND LINE ARGUMENTS
    section = "remote_RL" # in config_dict
    arguments = sys.argv[1:]
    config_dict = configparse.parse_args_to_param_dict(arguments, section)

    #READ PARAMETERS:
    controller_ip    = config_dict.get_option(section,'host')
    controller_port  = config_dict.get_option(section,'port')

    #START:
    remote = Remote(controller_ip, controller_port)
    remote.connect()
    remote.train()
    try:
        remote.run()
    finally:
        remote.stop()

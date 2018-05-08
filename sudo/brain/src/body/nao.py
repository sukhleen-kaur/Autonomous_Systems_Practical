import logging

import os
import util.nullhandler
import math
from ftplib import FTP, error_perm
import glob
import time

from util.euclid import Vector3 as V3

# Aldebaran Imports
try:
    from naoqi import ALProxy, ALModule, ALBroker
except:
    print "NAOQI Not available. Nao will not work, unless you are using FakeNao"
import motion

logging.getLogger('Borg.Brain.BodyController.Nao').addHandler(util.nullhandler.NullHandler())
    
class Nao(object):
    """
    Controls a nao
    """

    TO_RAD = math.pi / 180.0 
    ## Minimum and maximum ranges of joints
    __joint_range = {}

    def __init__(self, robot_ip, port=9559, nobody=False):
        self.logger = logging.getLogger('Borg.Brain.BodyController.Nao')
        self.__robot_ip = robot_ip
        self.__port = port
        self.__username = 'nao'
        self.__password = 'nao'
        self.__FM = ALProxy("ALFrameManager", robot_ip, int(port))
        try:
            # Local NaoQi does not have TTS, real robot does
            self.__TTS = ALProxy("ALTextToSpeech", robot_ip, int(port))
            ##self.__VisionTB = ALProxy("ALVisionToolbox", robot_ip, int(port)) # Doesn't work with NaoQi 2.x
            self.__Sonar = ALProxy("ALSonar", robot_ip, int(port))
            self.__Sonar.subscribe("Sonar",200,0.02)
            self.__BallTracker = ALProxy("ALRedBallTracker", robot_ip, int(port))
            self.simulation = False
        except Exception as e:
            print '[nao.py: init] Exception: ', e
            self.__TTS = None
            self.__VisionTB = None
            self.__Sonar = None
            self.__BallTracker = None
            self.simulation = True
        self.__BehaviorManager = ALProxy("ALBehaviorManager", robot_ip, int(port))
        self.__Posture = ALProxy("ALRobotPosture", robot_ip, int(port))
        self.__Motion = ALProxy("ALMotion", robot_ip, int(port))
        self.__Memory = ALProxy("ALMemory", robot_ip, int(port))
        self.__Video = ALProxy("ALVideoDevice", robot_ip, int(port))
        self.__Leds = ALProxy("ALLeds", robot_ip, int(port))
        self.__behaviorIDs = {}
        self.__stop_crouch = True
        self.__nobody = nobody

        # Enable TTS notifications, just in case (so we can determine if the nao is currently speaking or not):
        if not self.__TTS == None:
            try:
                self.__TTS.enableNotifications()
            except Exception as e:
                #TODO: Verify that the generated exception is caught only because notifications are already enabled.
                print e
        
        #Create LED Groups for NAO eyes or ears
        self.setLedsGroup()
        
        self.reset_fallen(); # Reset the fallen variable because it might still be set
        
    def has_fallen(self):
        try: 
            if (self.__Memory.getData("robotHasFallen")):
                self.__Motion.killAll(); # Kill all motions
                return True;
            else:
                return False;
        except:
            return False;

        
    def reset_fallen(self):
        try: 
            self.__Memory.removeData("robotHasFallen");
        
        except:
            pass;
        

    def is_bumper_pressed(self):
        return self.__Memory.getData("RightBumperPressed", 0) == 1.0 or self.__Memory.getData("LeftBumperPressed", 0) == 1.0

    def is_tactile_head_pressed_front(self):
        return self.__Memory.getData("FrontTactilTouched", 0) == 1.0

    def is_tactile_head_pressed_middle(self):
        return self.__Memory.getData("MiddleTactilTouched", 0) == 1.0

    def is_tactile_head_pressed_rear(self):
        return self.__Memory.getData("RearTactilTouched", 0) == 1.0

    def tasks_finished(self):
        print "Tasklist"
        print self.__Motion.getTaskList()
        if self.__Motion.getTaskList():
            return False
        return True

    def __del__(self):
        self.logger.info("NAO controller stopping, de-enslaving NAO")
        self.set_stifness(['Body'], [0], [0.25])
        if self.__Sonar:
            self.__Sonar.unsubscribe("Sonar")
        #self.__broker.shutdown()

    def stand_up(self, pose_name="Stand", speed=0.5):
        """
        Blocking call.
        Speed is relative between 0 and 1.
        Alternative names are: "StandInit", "StandZero".
        """
        self.__Posture.goToPosture(pose_name, speed)

    def stop(self):
        if self.__nobody:
            return

        print "De-enslaving Nao"
        self.stop_walking()
        print 'stopping walking'
        self.__Motion.rest()

    def setLedsGroup(self, names = None):
        if not names:
            # Create a new group
            names = [
            "Face/Led/Red/Left/0Deg/Actuator/Value",
            "Face/Led/Red/Left/90Deg/Actuator/Value",
            "Face/Led/Red/Left/180Deg/Actuator/Value",
            "Face/Led/Red/Left/270Deg/Actuator/Value",
            "Face/Led/Red/Right/0Deg/Actuator/Value",
            "Face/Led/Red/Right/90Deg/Actuator/Value",
            "Face/Led/Red/Right/180Deg/Actuator/Value",
            "Face/Led/Red/Right/270Deg/Actuator/Value"]
            self.__Leds.createGroup("MyGroup",names)

    def set_camera(self, name):
        if name == 'top':
            self.__Video.setActiveCamera(0)
        elif name == 'bottom':
            self.__Video.setActiveCamera(1)
        else:
            self.__Video.setActiveCamera(1)

    def move(self, Joint, Angle, Speed):
        self.__Motion.setAngles(Joint, Angle, Speed)

    def walk(self, X=0, Y=0, Theta=0):
        '''
        Start walking in a specified direction (X, Y) and with a specified rotation (Theta).
        All values should be given in the range [-1,1].
        Positive values: Forwards, left or counter-clockwise:
        Negative values: Backwards, right or clockwise.
        '''
        self.__Motion.moveToward(X, Y, Theta)

    def is_walking(self):
        return self.__Motion.moveIsActive()
        
    def stop_walking(self):
        self.__Motion.stopMove()
        
    def is_speaking(self):
        if self.simulation:
            return False
        else:
            is_done_speaking = self.__Memory.getData("ALTextToSpeech/TextDone")
            if not is_done_speaking == None:
                is_done_speaking = int(is_done_speaking)
                if is_done_speaking == 0:
                    return True
            return False

    def say(self, Text, filename=None):
        if self.__TTS:
            #self.__TTS.say(str(Text))
            if filename:
                self.__TTS.sayToFile(Text, filename)
            else:
                self.__TTS.post.say(Text)
        else:
            print "[Nao says] " + Text


    def get_sonar_distance(self):
#        sonarValue= "SonarLeftDetected"
        if self.__Sonar:
#            data = self.__Sonar.getOutputNames()
            data = {"left": self.__Memory.getData("SonarLeftDetected",0), "right" : self.__Memory.getData("SonarRightDetected",0)}
            return data

    def get_yaw_pitch(self, radians=True):
        #Get Nao's yaw and pitch neck angles in RADIANS:
        names  = "Body"
        useSensors  = True
        sensorAngle = self.__Motion.getAngles(names, useSensors)
        headYaw = sensorAngle[0]
        headPitch = sensorAngle[1]
        # If radians is false, return degrees
        if not radians:
            headYaw = headYaw / self.TO_RAD
            headPitch = headPitch / self.TO_RAD
        return [headYaw, headPitch]

    def get_robot_ip(self):
        '''
        Returns the IP address as specified in the constructor.
        '''
        return self.__robot_ip

    def get_port(self):
        '''
        Returns the port as specified in the constructor.
        '''
        return self.__port

    def get_installed_behaviors(self):
        return self.__BehaviorManager.getInstalledBehaviors()
    
    def is_behavior_running(self, behaviorID, behaviorname):
        behavior = str(behaviorID) + "/" + behaviorname;
        return self.__BehaviorManager.isBehaviorRunning(behavior);

    def start_behavior(self, behaviorID, behaviorname, local=False):
        """
        Start a behavior from Choregraphe which is stored on the robot.
        The local parameter specifies that the file should be loaded from the
        local filesystem instead of from the robot.
        This function requires a behavior ID and the behavior name, both of which
        can be found in Choregraphe when the behavior has been uploaded onto the Nao."
        """
        behavior = str(behaviorID) + '/' + behaviorname
        self.__BehaviorManager.startBehavior(behavior)

    def complete_behavior(self, behaviorID, behaviorname, local=False):
        """
        Start a behavior from choregraph which is stored on the robot. Waits for
        the behavior to finish. The behavior should call it's output, otherwise
        this method will get stuck
        The local parameter specifies that the file should be loaded from the
        local filesystem instead of from the robot.
        """
        behavior = str(behaviorID) + '/' + behaviorname
        self.__BehaviorManager.runBehavior(behavior)

    def get_behavior_id(self, behaviorname, local=False):
        """
        Before a xml file can be run, a behavior has to be created. If this
        was already done before, just get the behavior id from the `behaviorIDs'
        dictionary. Otherwise, create the behavior right now.
        The local parameter specifies that the file should be loaded from the
        local filesystem instead of from the robot.
        """
        path = "" # path within the xml file
        if local:
            if self.simulation:
                # Use FrameManager when using a simulated robot as FTP won't work
                xmlfile = os.environ['BORG'] + "/Brain/Choregraphs/" + behaviorname + "/behavior.xar"
                self.logger.debug("Loading contents of local file %s as behavior %s" % (xmlfile, behaviorname))
                try:
                    contents = open(xmlfile, 'r').read()
                    id = self.__FM.newBehavior(path, contents)
                    self.__behaviorIDs[behaviorname] = id
                    return id
                except:
                    self.logger.error("Unable to load contents of local file %s - does it exist?" % xmlfile);
            else:
                # Use FTP to transfer behavior to robot as its much faster
                if not self.store_behavior_on_nao(behaviorname):
                    self.logger.error("Unable to send behavior to Nao. Not executing")
                    self.say("I cannot load the requested behavior")
                    return None
        xmlfile = "/home/nao/behaviors/" + behaviorname + "/behavior.xar"
        self.logger.debug("Loading contents of file %s on the robot as behavior %s" % (xmlfile, behaviorname))
        id = self.__FM.newBehaviorFromFile(xmlfile, path)
        print id
        self.__behaviorIDs[behaviorname] = id
        return id


    def set_stiffness(self,
                      names=['Body', 'Body', 'Body'],
                      stiffnessLists=[0.25, 0.5, 1.0],
                      timeLists=[0.5, 1.0, 1.5]):
        self.set_stifness(names, stiffnessLists, timeLists)

    def set_stifness(self,
                     names=['Body', 'Body', 'Body'],    # Part of the robot to apply to
                     stiffnessLists = [0.25, 0.5, 1.0], # Trajectory of stiffness levels
                     timeLists = [0.5, 1.0, 1.5]):      # Time
        """
        The stiffnessLiss is a list of stiffness levels. Each entry sets the
        stiffnesslevel that should be set at the time specified in the same
        element in the timeLists
        """
        for i in range(len(names)):
            self.__Motion.stiffnessInterpolation(names[i], stiffnessLists[i], timeLists[i])

    def get_range(self, name, radian=False):
        """
        This method wraps the getLimits function of naoqi; it caches the results
        because each call to ALMotion.getLimits takes a lot of time
        """
        if not name in self.__joint_range:
            limits = self.__Motion.getLimits(name)
            self.__joint_range[name] = limits[0]

        val = self.__joint_range[name]
        if not radian:
            val = (val[0] / self.TO_RAD,
                   val[1] / self.TO_RAD)

        return val

    def change_angles(self, names, angles, max_speed, disable_stiffness=False, radians=False):
        """
        This method will change the angles for the joints in the list of names.
        Joints will have to be stiffened first for this function to take effect.
        """
        if not radians:
            angles = [x * self.TO_RAD for x in angles]

        # Perform te movement
        self.__Motion.changeAngles(names, angles, max_speed)

    def set_angles(self, names, angles, max_speed, disable_stiffness=False, radians=False):
        """
        This method will set the angles for the joints in the list of names.
        Joints will have to be stiffened first for this function to take effect.
        """
        if not radians:
            angles = [x * self.TO_RAD for x in angles]

        # Perform the movement
        self.__Motion.setAngles(names, angles, max_speed)

    def get_angles(self, names, radians=False, use_sensors=False):
        useSensors  = False     # Cannot use sensors in simulation :(
        angles = self.__Motion.getAngles(names, useSensors)
        if not radians:
            angles = [x / self.TO_RAD for x in angles]
        return angles

    def get_proxy(self, which = "motion"):
        if which == "motion":
            return self.__Motion
        elif which == "tts":
            return self.__TTS
        elif which == "video":
            return self.__Video
        elif which == "frame":
            return self.__FM
        elif which == "memory":
            return self.__Memory
        elif which == "vision":
            return self.__VisionTB
        elif which == "balltracker":
            return self.__BallTracker

    def emergency(self):
        """Disable the NAO stiffness so it stops moving"""
        self.logger.warn("Emergency button pressed")
        self.set_stifness(['Body'], [0], [0.25])
        #self.say("My emergency button has been pressed. I am now in emergency mode")
    
    def emergencyLeds(self, mode):
        
        if mode:
            # Switch the new group on
            self.__Leds.on("MyGroup")
        else:
            # Switch the new group on
            self.__Leds.off("MyGroup")
    


    def init_pose(self, kneeAngle=20, torsoAngle=0, wideAngle=0, start_wide=False, skip_legs=False):
        """
        This method initializes the grabbing pose. It is adapted from the 
        example in the Aldebaran NAO documentation
        """
        # Enable stiffness to move
        if skip_legs:
            self.set_stiffness()
        else:
            self.set_stifness(names=['LArm', 'RArm', 'Head'],
                              stiffnessLists=[1.0, 1.0, 1.0],
                              timeLists=[0.5, 0.5, 0.5])

        ###############################################################################
        # PREPARE THE ANGLES
        ###############################################################################
        # Define The Initial Position
        Head     = [0, 0]
        if start_wide:
            LeftArm  = [0,  90, -30, -20]
        else:
            LeftArm  = [75,  15, -30, -20]
        
        if skip_legs:
            wideAngle = 0
            kneeAngle = 2.16 / self.TO_RAD
            torsoAngle = 0

        LeftLeg  = [0,  wideAngle, -kneeAngle/2-torsoAngle, kneeAngle, -kneeAngle/2, -wideAngle]
        RightLeg = [0, -wideAngle, -kneeAngle/2-torsoAngle, kneeAngle, -kneeAngle/2,  wideAngle]

        if start_wide:
            RightArm = [0, -90,  30,  20]
        else:
            RightArm = [75, -15,  30,  20]
        
        if start_wide:
            LeftArm  += [-90, 1 / self.TO_RAD]
            RightArm += [90, 1 / self.TO_RAD]
        else:
            LeftArm  += [-60, 1 / self.TO_RAD]
            RightArm += [60, 1 / self.TO_RAD]

        # Gather the joints together
        pTargetAngles = Head + LeftArm + LeftLeg + RightLeg + RightArm

        # Convert to radians
        pTargetAngles = [x * self.TO_RAD for x in pTargetAngles]

        ###############################################################################
        # SEND THE COMMANDS
        ###############################################################################
        # We use the "Body" name to signify the collection of all joints
        pNames = "Body"

        # We set the fraction of max speed
        pMaxSpeedFraction = 0.2

        # Ask motion to do this with a blocking call
        self.__Motion.angleInterpolationWithSpeed(pNames, pTargetAngles, pMaxSpeedFraction)

        # Disable stiffness of the arms, but not the legs
        self.set_stifness(['LArm', 'RArm', 'Head'], [0, 0, 0], [0.25, 0.25, 0.25])

    def sit_down(self):
        """
        This method lets the NAO sit down in a stable crouching position and 
        removes stiffness when done.
        """
        return 
        # Enable stiffness to move
        self.set_stifness(['Body'], [0.25], [0.25])

        ###############################################################################
        # PREPARE THE ANGLES
        ###############################################################################
        # Define The Sitting Position
        pNames  = ['LAnklePitch', 'LAnkleRoll', 'LHipPitch', 'LHipRoll', 'LHipYawPitch', 'LKneePitch', 
                   'RAnklePitch', 'RAnkleRoll', 'RHipPitch', 'RHipRoll', 'RHipYawPitch', 'RKneePitch',
                   'LShoulderPitch', 'RShoulderPitch', 'HeadYaw', 'HeadPitch']

        pAngles = [        -1.21,        0.036,      -0.700,     -0.027,         -0.143,         2.16,
                           -1.21,       -0.036,      -0.700,      0.027,         -0.143,         2.16,
                            0.96,         0.96,           0,          0]


        ###############################################################################
        # SEND THE COMMANDS
        ###############################################################################
        # We set the fraction of max speed
        pMaxSpeedFraction = 0.2

        # Ask motion to do this with a blocking call
        self.__Motion.angleInterpolationWithSpeed(pNames, pAngles, pMaxSpeedFraction)

        # Disable stiffness 
        self.set_stifness(['Body'], [0], [0.25])

    def look_straight(self):
        self.set_angles(['HeadYaw', 'HeadPitch'], [0, 0], 0.2, radians=True)

    


#########
# NOTES #
#########

# Nao's head movement range in RADIANS when reading them directly from ALMemory:
#
# YAW:
# left   (+):  2.08566856384
# right  (-): -2.08566856384
#
# PITCH:
# Bottom (+):  0.514872133732
# Top    (-): -0.671951770782
#
# The robot needs to have the head pitch at least
# at 0.06 radians to be able to turn the head
# completely to both sides (left or right). If its
# head pith is smaller (i.e. looking further up) the
# ethernet cable in his head will get stocked with
# its shoulders.
#
# Changes in the order of 1/1000 of a radian (aprox 0.057 degrees)
# are not noticeable anymore, it is not necessary to
# be more precise than that when giving it commands.
#

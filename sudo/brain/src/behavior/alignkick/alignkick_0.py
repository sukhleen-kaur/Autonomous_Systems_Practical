

'''
this is an automatically generated template, if you don't rename it, it will be overwritten!
'''

import basebehavior.behaviorimplementation
import rospy


class Alignkick_x(basebehavior.behaviorimplementation.BehaviorImplementation):

    '''this is a behavior implementation template'''

    #this implementation should not define an __init__ !!!


    def implementation_init(self):

	self.__nao = self.body.nao(0)
	self.__start_time = rospy.Time.now().to_sec()
	self.__nao.set_camera('bottom') 
	self.__state = "WAIT"
	self.last_ball_recogtime = rospy.Time.now().to_sec()
	self.__pitch_angle = self.__nao.get_yaw_pitch()
	self.midX = 0
	self.midY = 0
        pass

    def implementation_update(self):

	if (self.m.n_occurs("colorblob_red") > 0):
		(recogtime, obs) = self.m.get_last_observation("colorblob_red")
		if recogtime > self.last_ball_recogtime:
			blob = obs['1']
			self.midX = blob['x'] + blob['width']/2
			self.midY = blob['y'] + blob['height']/2
			if abs(blob['width'] - blob['height']) < 2:
				self.last_ball_recogtime = recogtime
				if self.__state == "WAIT":
					self.__state = "ALIGNING_KICK"

	if self.__nao.has_fallen():
		self.set_failed("I fell")

	elif (rospy.Time.now().to_sec() - self.last_ball_recogtime) > 3:
			self.__nao.stop_walking()
			self.set_failed("I lost the ball")
	
	elif self.__state == "ALIGNING_KICK":
		if self.midX > 139:
			self.__nao.walk(0, -0.3, 0)
		elif self.midX < 128:
			self.__nao.walk(0, 0.3, 0)
		elif self.midY <= 195:
			self.__nao.walk(0.2, 0, 0.05)
		elif (self.__nao.is_bumper_pressed() or self.midY > 195) and (rospy.Time.now().to_sec() - self.last_ball_recogtime < 2):
			self.__nao.stop_walking()
			self.__state = "KICKING"

	elif self.__state == "KICKING":
		self.__nao.get_installed_behaviors()
		self.__nao.complete_behavior("nao_kick_3-50c605", "behavior_1")
		self.set_finished()

        pass




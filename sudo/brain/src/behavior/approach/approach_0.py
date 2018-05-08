

'''
this is an automatically generated template, if you don't rename it, it will be overwritten!
'''

import basebehavior.behaviorimplementation
import rospy

class Approach_x(basebehavior.behaviorimplementation.BehaviorImplementation):

    '''this is a behavior implementation template'''

    #this implementation should not define an __init__ !!!


    def implementation_init(self):
	self.__nao = self.body.nao(0)
	self.__start_time = rospy.Time.now().to_sec()
	self.__screen_center_X = 320/2
	self.__screen_center_Y = 240/2
	self.__nao.set_camera('bottom')
	self.__state = "WAIT"
	self.last_ball_recogtime = rospy.Time.now().to_sec()
	self.last_ball_time = rospy.Time.now().to_sec()
	self.__counter = 0
	self.midX = 160
	self.midY = 120
        pass

    def implementation_update(self):
	pitch_angle = self.__nao.get_yaw_pitch()
	if self.__nao.has_fallen():
		self.set_failed("I fell down")

	if rospy.Time.now().to_sec() - self.last_ball_recogtime > 3:
		self.set_failed("I lost the ball from my vision")

	if (self.m.n_occurs("colorblob_red") > 0):
		(recogtime, obs) = self.m.get_last_observation("colorblob_red")
		if recogtime > self.last_ball_recogtime:
			blob = obs['1']
			self.midX = blob['x'] + blob['width']/2
			self.midY = blob['y'] + blob['height']/2
			if abs(blob['width'] - blob['height']) < 2:
				self.last_ball_recogtime = recogtime
				self.__state = "APPROACH"

	if self.__state == "APPROACH":

		if self.midY - self.__screen_center_Y > 10:
			self.__nao.move('HeadPitch', pitch_angle[1]+0.05, 0.4)
		elif self.__screen_center_Y - self.midY > 10:
			self.__nao.move('HeadPitch', pitch_angle[1]-0.05, 0.4)
		if (self.midX - self.__screen_center_X) > 10:
			move_angle = -0.1
		elif (self.__screen_center_X - self.midX) > 10:
			move_angle = 0.1
		else:
			move_angle = 0
		if pitch_angle[1] < 0.2:
			speed = 0.7
		else:
			speed = 0.3

		self.__nao.walk(speed, 0, move_angle)

		if pitch_angle[1] > 0.32:
			self.__state = "APPROACHING_1"
			

	if self.__state == "APPROACHING_1":
		if self.__counter > 20:
			self.__counter = 0
			self.__nao.stop_walking()
			self.set_finished()
		else:
			self.__nao.walk(0.05, 0, 0)
			self.__counter += 1
			
	pass



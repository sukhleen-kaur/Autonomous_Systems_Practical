
'''
this is an automatically generated template, if you don't rename it, it will be overwritten!
'''

import basebehavior.behaviorimplementation
import rospy


class Aligngoal_x(basebehavior.behaviorimplementation.BehaviorImplementation):

    '''this is a behavior implementation template'''

    #this implementation should not define an __init__ !!!


    def implementation_init(self):

	self.__nao = self.body.nao(0)
	self.__start_time = rospy.Time.now().to_sec()
	self.__screen_center_X = 320/2
	self.__screen_center_Y = 240/2
	self.__nao.set_camera('bottom')   
	self.__state = "LOOK"
	self.__head_movement = "LEFT"
	self.last_goal_recogtime = rospy.Time.now().to_sec()
	self.midX = 0
	self.midY = 0
	self.counter = 0;
        pass

    def implementation_update(self):
	self.__yaw_angle = self.__nao.get_yaw_pitch()
	if (self.m.n_occurs("colorblob_yellow") > 0):
		(recogtime, obs) = self.m.get_last_observation("colorblob_yellow")
		if recogtime > self.last_goal_recogtime:
			blob = obs['1']
			self.midX = blob['x'] + blob['width']/2
			self.midY = blob['y'] + blob['height']/2
            if blob['width'] * blob['height'] > 3500:
                self.last_goal_recogtime = recogtime
			if self.__state == "LOOK" or self.__state == "FOUND_GOAL_LEFT":
				self.__state = "FOUND_GOAL"

	if self.__nao.has_fallen():
		self.set_failed("I fell")

	#if (rospy.Time.now().to_sec() - self.last_goal_recogtime) > 5 and self.__state == "FOUND_GOAL":
		#self.__state = "LOOK"
		#self.__head_movement = "LEFT"
		
	elif (rospy.Time.now().to_sec() - self.__start_time) > 1 and self.__state == "LOOK":
		if self.__head_movement == "LEFT":
			if self.__yaw_angle[0] < 0.9:
				self.__nao.move('HeadYaw', self.__yaw_angle[0]+0.07, 0.13)
			elif self.__yaw_angle[0] >= 0.9:
				self.__head_movement = "STRAIGHT"
				self.__nao.move('HeadYaw', 0, 0.4)
		else:
			self.__nao.walk(0, 0.41, -0.145)
			
	elif self.__state == "FOUND_GOAL" and abs(self.__screen_center_X - self.midX) < 3:
		self.__nao.stop_walking()
		self.set_finished()
	
	elif self.__state == "FOUND_GOAL" and self.__head_movement == "LEFT":
		self.__head_movement = "STRAIGHT"
		self.__nao.move('HeadYaw', 0, 0.5)
		self.__state = "WAIT"

	elif self.__state == "FOUND_GOAL":
		if self.midX < self.__screen_center_X:
			self.__nao.walk(0,-0.41,0.145)
		elif self.midX > self.__screen_center_X:
			self.__nao.walk(0,0.41,-0.145)
			
	elif self.__state == "WAIT":
		if self.counter > 10:
			self.counter = 0
			self.__state = "FOUND_GOAL_LEFT"
		else:
			self.counter += 1
			
	elif self.__state == "FOUND_GOAL_LEFT":
		self.__nao.walk(0, -0.41, 0.145)


        #you can do things here that are low-level, not consisting of other behaviors

        #in this function you can check what behaviors have failed or finished
        #and do possibly other things when something has failed
        pass





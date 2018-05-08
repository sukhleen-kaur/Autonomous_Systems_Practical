'''
this is an automatically generated template, if you don't rename it, it will be overwritten!
'''

import basebehavior.behaviorimplementation

import rospy


class Findball_x(basebehavior.behaviorimplementation.BehaviorImplementation):

    #this implementation should not define an __init__ !!!


    def implementation_init(self):

	self.__nao = self.body.nao(0)
	self.__start_time = rospy.Time.now().to_sec()
	self.__screen_center = 320/2
	self.__nao.set_camera('bottom')
	self.__nao.stand_up()
	self.__nao.move('HeadPitch', -0.25, 0.4)
	self.__head_movement = "UPWARD"    
	self.__state = "LOOK"
	self.__yaw_movement = "LEFT"
	self.last_ball_recogtime = rospy.Time.now().to_sec()
	self.__pitch_angle = self.__nao.get_yaw_pitch()
	self.midX = 0
	self.midY = 0
        pass

    def implementation_update(self):	
	self.__pitch_angle = self.__nao.get_yaw_pitch()
	
	if (self.m.n_occurs("colorblob_red") > 0):
		(recogtime, obs) = self.m.get_last_observation("colorblob_red")
		if recogtime > self.last_ball_recogtime:
			blob = obs['1']
			self.midX = blob['x'] + blob['width']/2
			self.midY = blob['y'] + blob['height']/2
			#if the object's width and height is almost identical, it is likely to be the ball
			if abs(blob['width'] - blob['height']) < 2:
				
				if (self.__state == "LOOK" and (self.__yaw_movement == "LEFT" or self.__yaw_movement == "RIGHT") and self.__pitch_angle[0] < 0.1)  or (self.__state == "FOUND_BALL_LEFT" and (rospy.Time.now().to_sec() - self.last_ball_recogtime) > 0.3) or (self.__state == "LOOK" and self.__yaw_movement == "STRAIGHT"):
					self.__nao.move('HeadYaw', 0, 0.5)
					self.__yaw_movement = "STRAIGHT"
					self.__state = "FOUND_BALL"
					if self.__pitch_angle[1] < 0.35:
						self.__nao.move('HeadPitch', self.__pitch_angle[1], 0.2)
					else:
						self.__nao.move('HeadPitch', 0.41, 0.2)

				elif self.__state == "LOOK" and (self.__yaw_movement == "LEFT" or self.__yaw_movement == "RIGHT"):
					self.__state = "FOUND_BALL_LEFT"
					self.__nao.move('HeadYaw', 0, 0.5)
					self.__yaw_movement = "STRAIGHT"
				self.last_ball_recogtime = recogtime
					
					
	if self.__nao.has_fallen():
		self.set_failed("I fell")
		
	elif rospy.Time.now().to_sec() - self.last_ball_recogtime > 5 and self.__state == "FOUND_BALL":
		self.set_failed("I lost the ball")
		
	elif rospy.Time.now().to_sec() - self.last_ball_recogtime > 10 and self.__state == "FOUND_BALL_LEFT":
		self.set_failed("I lost the ball")

	#stop walking/moving when the ball is around the center of the vision field
	elif self.__state == "FOUND_BALL" and abs(self.__screen_center - self.midX) < 5:
		if self.midY > 150:
			self.__nao.move('HeadPitch', self.__pitch_angle[1]+0.1, 0.3)
		elif self.midY < 90:
			self.__nao.move('HeadPitch', self.__pitch_angle[1]-0.1, 0.3)
		self.__nao.stop_walking()
		self.__state == "FINISHED"
		
	#once found the ball, turn slower
	elif self.__state == "FOUND_BALL":
		if self.midX < self.__screen_center:
			self.__nao.walk(0,0,0.1)
		elif self.midX > self.__screen_center:
			self.__nao.walk(0,0,-0.1)
			
	elif self.__state == "FOUND_BALL_LEFT":
		self.__nao.walk(0, 0, 0.3)
			
	elif (rospy.Time.now().to_sec() - self.__start_time) > 1:
		if self.__state == "LOOK":
			if self.__yaw_movement == "LEFT":
				if self.__pitch_angle[0] < 0.7:
					self.__nao.move('HeadYaw', self.__pitch_angle[0]+0.07, 0.13)
				elif self.__pitch_angle[0] >= 0.7:
					self.__nao.move('HeadPitch', 0.3, 0.4)
					self.__yaw_movement = "RIGHT"
			elif self.__yaw_movement == "RIGHT":
				if self.__pitch_angle[0] > 0.3:
					self.__nao.move('HeadYaw', self.__pitch_angle[0]-0.07, 0.13)
				elif self.__pitch_angle[0] <= 0.3:
					self.__nao.move('HeadYaw', 0, 0.5)
					self.__yaw_movement = "STRAIGHT"
			elif self.__yaw_movement == "STRAIGHT":
				#turn clockwise
				self.__nao.walk(0, 0, -0.3)
				#change the direction of the head movement if it reaches a certain point
				if self.__pitch_angle[1] > 0.41 and self.__head_movement == "DOWNWARD":
					self.__head_movement = "UPWARD"
				elif self.__pitch_angle[1] <= -0.3 and self.__head_movement == "UPWARD":
					self.__head_movement = "DOWNWARD"
					#move the head (pitch)
				if self.__head_movement == "UPWARD":
					self.__nao.move('HeadPitch', -0.4, 0.07)
				elif self.__head_movement == "DOWNWARD":
					self.__nao.move('HeadPitch', 0.42, 0.07)

			


        #you can do things here that are low-level, not consisting of other behaviors

        #in this function you can check what behaviors have failed or finished
        #and do possibly other things when something has failed
        pass

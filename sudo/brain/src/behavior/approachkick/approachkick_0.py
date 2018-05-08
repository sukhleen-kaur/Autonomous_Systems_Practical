
'''
this is an automatically generated template, if you don't rename it, it will be overwritten!
'''

import basebehavior.behaviorimplementation
import rospy


class Approachkick_x(basebehavior.behaviorimplementation.BehaviorImplementation):

    '''this is a behavior implementation template'''

    #this implementation should not define an __init__ !!!


    def implementation_init(self):
	self.__nao = self.body.nao(0)
	self.__start_time = rospy.Time.now().to_sec()
	self.__screen_center_X = 320/2
	self.__screen_center_Y = 240/2
	self.createSubbehavior()
	self.startSearching = False
	self.selected_behaviors = [('mySearch',"self.startSearching == True")]
	self.__nao.set_camera('bottom')
	self.__state = "SEARCH"
	self.__nao.stand_up()
	self.last_ball_recogtime = rospy.Time.now().to_sec()
	self.__counter = 0
        pass

    def createSubbehavior(self):
	self.startSearching = False
	self.mySearch = self.ab.searchmain({})

    def implementation_update(self):
	if self.__nao.has_fallen():
		self.__nao.stand_up()
		self.__state = "SEARCH"
		self.__counter = 0



	if self.__state == "SEARCH":
		
		self.createSubbehavior()
		self.startSearching = True
		self.__state = "runningSearch"



	if self.__state == "runningSearch" and self.mySearch.is_finished():
		self.startSearching = False
		self.__state = "WAIT"
	if self.__state == "WAIT": ###
		if self.__counter == 0:
			self.__nao.stand_up()
		self.__counter += 1
		if self.__counter > 10:
			self.__counter = 0
			self.__state = "APPROACH"

	if (self.m.n_occurs("colorblob_red") > 0) and not self.__state == "runningSearch":
		(recogtime, obs) = self.m.get_last_observation("colorblob_red")
		if recogtime > self.last_ball_recogtime:
			blob = obs['1']
			midX = blob['x'] + blob['width']/2
			midY = blob['y'] + blob['height']/2
		if (rospy.Time.now().to_sec() - recogtime) > 6:
			self.__nao.stop_walking()
			self.__state = "SEARCH"
			self.__counter = 0
	
	if self.__state == "APPROACH":
		pitch_angle = self.__nao.get_yaw_pitch()
		if midY - self.__screen_center_Y > 10:
			self.__nao.move('HeadPitch', pitch_angle[1]+0.05, 0.2)
		elif self.__screen_center_Y - midY > 10:
			self.__nao.move('HeadPitch', pitch_angle[1]-0.05, 0.2)
		if (midX - self.__screen_center_X) > 10:
			move_angle = -0.1
		elif (self.__screen_center_X - midX) > 10:
			move_angle = 0.1
		else:
			move_angle = 0
		self.__nao.walk(0.7, 0, move_angle)
		if pitch_angle[1] > 0.50:
			self.__state = "PREPARE_KICK"
			self.__nao.stop_walking()
		
	if self.__state == "PREPARE_KICK":
		if midX > 150:
			self.__nao.walk(0, -0.3, 0)
		elif midX < 120:
			self.__nao.walk(0, 0.3, 0)
		else:
			self.__nao.walk(0.2, 0, 0)
		if (self.__nao.is_bumper_pressed() or midY > 170) and (rospy.Time.now().to_sec() - recogtime < 3): ###
			self.__nao.stop_walking()
			self.__state = "KICK"

	if self.__state == "KICK":
		self.__nao.get_installed_behaviors()
		self.__nao.complete_behavior("naokick-aedf99", "behavior_1")
		self.__state = "DONE"

	


        #you can do things here that are low-level, not consisting of other behaviors

        #in this function you can check what behaviors have failed or finished
        #and do possibly other things when something has failed
        pass





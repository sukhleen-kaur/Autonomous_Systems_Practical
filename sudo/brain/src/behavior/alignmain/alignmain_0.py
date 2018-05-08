

'''
this is an automatically generated template, if you don't rename it, it will be overwritten!
'''

import basebehavior.behaviorimplementation
import rospy


class Alignmain_x(basebehavior.behaviorimplementation.BehaviorImplementation):

    '''this is a behavior implementation template'''

    #this implementation should not define an __init__ !!!


    def implementation_init(self):
	self.__nao = self.body.nao(0)
	self.__start_time = rospy.Time.now().to_sec()
	self.__screen_center_X = 320/2
	self.__screen_center_Y = 240/2
	self.createSearchBehavior()
	self.startSearching = False
	self.createApproachBehavior()
	self.startApproaching = False
	self.createAlignGoalBehavior()
	self.startGoalAligning = False
	self.createAlignKickBehavior()
	self.startKicking = False
	self.selected_behaviors = [('mySearch',"self.startSearching == True"), ('myApproach', "self.startApproaching == True"), ('myAlignGoal',"self.startGoalAligning == True"),('myKick',"self.startKicking == True")]
	self.__nao.set_camera('bottom')
	self.__state = "SEARCH"
	self.__nao.stand_up()
	self.last_ball_recogtime = rospy.Time.now().to_sec()
	self.__counter = 0
        pass

    def createSearchBehavior(self):
	self.startSearching = False
	self.mySearch = self.ab.searchmain({})
        pass

    def createApproachBehavior(self):
	self.startApproaching = False
	self.myApproach = self.ab.approach({})
        pass

    def createAlignGoalBehavior(self):
	self.startGoalAligning = False
	self.myAlignGoal = self.ab.aligngoal({})
	pass

    def createAlignKickBehavior(self):
	self.startKicking = False
	self.myKick = self.ab.alignkick({})
	pass

    def implementation_update(self):
	if self.__state == "SEARCH":
		self.createSearchBehavior()
		self.startSearching = True
		self.__state = "RUNNING_SEARCH"
	elif self.__state == "RUNNING_SEARCH" and self.mySearch.is_finished():
		self.startSearching = False
		self.pitchAngle = self.__nao.get_yaw_pitch()[1]
		self.__nao.stand_up()
		self.__state = "WAIT"
	elif self.__state == "RUNNING_SEARCH" and self.mySearch.is_failed():
		self.startSearching = False
		self.__nao.stop_walking()
		self.__nao.stand_up()
		self.__nao.reset_fallen()
		self.__state = "SEARCH"

	elif self.__state == "WAIT":
		self.__nao.move('HeadPitch', self.pitchAngle, 0.3)
		self.__counter += 1
		if self.__counter > 3:
			self.__counter = 0
			self.__state = "APPROACH"

	elif self.__state == "APPROACH":
		self.createApproachBehavior()
		self.startApproaching = True
		self.__state = "RUNNING_APPROACH"
	elif self.__state == "RUNNING_APPROACH" and self.myApproach.is_finished():
		self.startApproaching = False
		self.__nao.stand_up()
		self.__state = "WAIT_2"
	elif self.__state == "RUNNING_APPROACH" and self.myApproach.is_failed():
		self.startApproaching = False
		self.__nao.stop_walking()
		self.__nao.stand_up()
		self.__nao.reset_fallen()
		self.__state = "SEARCH"

	elif self.__state == "WAIT_2":
		self.__nao.move('HeadPitch', -0.4, 0.4)
		self.__counter += 1
		if self.__counter > 3:
			self.__counter = 0
			self.__state = "ALIGN_GOAL"
        
	elif self.__state == "ALIGN_GOAL":
		self.createAlignGoalBehavior()
		self.startGoalAligning = True
		self.__state = "ALIGNING_GOAL"
	elif self.__state == "ALIGNING_GOAL" and self.myAlignGoal.is_finished():
		self.startGoalAligning = False
		self.__state = "WAIT_3"
	elif self.__state == "ALIGNING_GOAL" and self.myAlignGoal.is_failed():
		self.startGoalAligning = False
		self.__nao.stop_walking()
		self.__nao.stand_up()
		self.__nao.reset_fallen()
		self.__state = "SEARCH"

	elif self.__state == "WAIT_3":
		self.__nao.move('HeadPitch', 0.41, 0.4)
		self.__counter += 1
		if self.__counter > 3:
			self.__counter = 0
			self.__state = "KICK"

	elif self.__state == "KICK":
		self.createAlignKickBehavior()
		self.startKicking = True
		self.__state = "KICKING"

	elif self.__state == "KICKING" and self.myKick.is_finished():
		self.startKicking = False
		self.__nao.stand_up()
		self.__state = "SEARCH"

	elif self.__state == "KICKING" and self.myKick.is_failed():
		self.startKicking = False
		self.__nao.stop_walking()
		self.__nao.stand_up()
		self.__nao.reset_fallen()
		self.__state = "SEARCH"


        pass




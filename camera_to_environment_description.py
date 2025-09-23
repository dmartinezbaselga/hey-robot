import rospy

import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import time

import process_visuals
from util.logging import print_value
from util.timer import TimerCollection


class CameraToEnvironmentDescription:
    def __init__(self, callback, rate=10, camera_topic="/rviz1/camera1/image"):
        
        self.callback = callback
        
        self.bridge = CvBridge()
        self.last_capture_time = rospy.Time.now()
        self.capture_interval = rospy.Duration(rate)  # 10 seconds interval
        self.image_sub = rospy.Subscriber(camera_topic, Image, self.image_callback)
        self.environment_description = "A crowded, spacious corridor"

    def image_callback(self, data):
        current_time = rospy.Time.now()
        if current_time - self.last_capture_time >= self.capture_interval:
            try:
                cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
            except CvBridgeError as e:
                rospy.logerr("CvBridge Error: {0}".format(e))
                return

            # Convert the image to PNG
            ret, png_image = cv2.imencode('.png', cv_image)
            if ret:
                self.analyze_environment(png_image)

            self.last_capture_time = current_time

    def analyze_environment(self, image):
      self.environment_description, is_different = process_visuals.explain_image(image, self.environment_description)
      if not is_different:
        # print('Environment from camera did not change')
        return
      self.callback(self.environment_description)

class CameraToEnvironmentDescriptionOnDemand:
    def __init__(self, camera_topic="/rviz1/camera1/image"):
            
        self.bridge = CvBridge()
        self.last_capture_time = rospy.Time.now()
        self.image_sub = rospy.Subscriber(camera_topic, Image, self.image_callback)
        self.environment_description = "A crowded, spacious corridor"
        self.data = None
        self.timing = TimerCollection("Camera")

    def image_callback(self, data):
        self.data = data

    def analyze_environment(self):
        if self.data is not None:
            try:
                cv_image = self.bridge.imgmsg_to_cv2(self.data, "bgr8")
            except CvBridgeError as e:
                rospy.logerr("CvBridge Error: {0}".format(e))
                return False

            # Convert the image to PNG
            ret, png_image = cv2.imencode('.png', cv_image)
            if ret:
                self.environment_description, is_different = process_visuals.explain_image(png_image, self.environment_description)
                cv2.imwrite("results/camera_images/" + self.environment_description.replace(" ", "_") + ".png", cv_image)
                return is_different
        else:
            return False

class OfflineCameraToEnvironment:        
    def __init__(self):
        self.environment_description = None
        self.timing = TimerCollection("Camera")

    def analyze_photo(self, img_path):
        cv_image = cv2.imread(img_path)

        # Convert the image to PNG
        ret, png_image = cv2.imencode('.png', cv_image)
        if ret:
            self.timing.start()
            self.environment_description, is_different = process_visuals.explain_image(png_image, self.environment_description)
            self.timing.stop()
            # cv2.imwrite("results/camera_images/" + self.environment_description.replace(" ", "_") + ".png", cv_image)
            return is_different
        



from selenium import selenium
import unittest

class ScreenshotGen(unittest.TestCase):
	def setUp(self):
		self.base_dir= "http://localhost/gothub/web/static/"
		self.image_dir = "/Users/evan/Desktop"
		self.selenium = selenium("localhost", \
			4444, "*firefox", self.base_dir)
		self.selenium.start()

	def test_google(self):
		sel = self.selenium
		base_path = self.base_dir + "map.html?project="
		projects = ["rails1", "rails", "homebrew", "dotfiles", "git", "perl", "node", "mono", "cucumber", "docrails", "progit"]
		for p in projects:
			sel.open(base_path+p)
			sel.window_maximize()
			#sel.wait_for_page_to_load(10000)
			#sel.click("map")
			sel.capture_entire_page_screenshot(self.image_dir+p+".png", None)
			
	def tearDown(self):
		self.selenium.stop()

if __name__ == "__main__":
	unittest.main()

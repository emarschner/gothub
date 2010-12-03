

from selenium import selenium
import unittest

class ScreenshotGen(unittest.TestCase):
	def setUp(self):
		self.base_dir= "http://localhost/gothub/web/static/"
		self.image_dir = "/Users/evan/Desktop/gothub/"
		self.cumulative = False
		self.byDate = False
		self.selenium = selenium("localhost", \
			4444, "*firefox", self.base_dir)
		self.selenium.start()

	def test_google(self):
		sel = self.selenium
		base_path = self.base_dir + "map.html?project="
		projects = ["rails1", "rails", "homebrew", "dotfiles", "git", "perl", "node", "mono", "cucumber", "docrails", "progit"]
		months = self.getMonthArr("10/2010", "12/2010")
		dateStart = months[0][0]+"/1/"+months[0][1]
		for p in projects:
			for i in range(0,len(months)-1):
				if self.byDate:
					if self.cumulative:
						path = base_path+p+"&date_start="+dateStart+"&date_end="+months[i+1][0]+"/1/"+months[i+1][1]
						imgName = p+"-cum-"+'-'.join(months[i])
					else:
						path = base_path+p+"&date_start="+months[i][0]+"/1/"+months[i][1] \
							+"&date_end="+months[i+1][0]+"/1/"+months[i+1][1]
						imgName = p+"-"+'-'.join(months[i])
				else:
					path = base_path+p
					imgName = p
				sel.open(path)
				sel.window_maximize()
				#sel.wait_for_page_to_load(10000)
				#sel.click("map")
				sel.capture_entire_page_screenshot(self.image_dir+imgName+".png", None)
			
	def tearDown(self):
		self.selenium.stop()
	
	def getMonthArr(self, s_date, e_date):
		s_date = s_date.split('/')
		s_month = int(s_date[0])
		s_year = int(s_date[1])
		cur_month = s_month
		cur_year = s_year
		e_date = e_date.split('/')
		e_month = int(e_date[0])
		e_year = int(e_date[1])
		retVal = []
		while True:
			end = False
			if cur_month == e_month and cur_year == e_year:
				end = True
			retVal.append((str(cur_month), str(cur_year)))
			cur_month = cur_month + 1
			if cur_month > 12:
				cur_month = 1
				cur_year = cur_year + 1
			if end:
				break
	
		return retVal

if __name__ == "__main__":
	unittest.main()

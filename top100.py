#Requires https://github.com/adoxa/ansicon to run on windows cmd (cleanly) -ILiedAboutCake 2015.
#also needs requests library on windows, get it with "python -m pip install -U requests"
import threading
import urllib2
import Queue
import json
import time
import csv

threadCount = 15 #define threads as a static number or use, len(strims) to run each as a thread. 
sleepTime = 60 #define time to reload the queue
topStrims = 100 #top number of twitch users to track
endpoint = "https://api.twitch.tv/kraken/streams"

queue = Queue.Queue()

#sets colored console stuffs
class bcolors:
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'

def timeMeme():
	return time.strftime("%d/%m/%y %H:%M:%S", time.localtime())

#updates the streamer queue
class StreamerGet(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name
	def run(self):
		while True:
			try:
			    api = urllib2.urlopen(endpoint + '?limit=' + str(topStrims))
			except urllib2.HTTPError as e:
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): API Failed (top100). Code " + str(e.code)
				skipCSV = True
			except urllib2.URLError as e:
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): API Failed (top100). Code " + str(e.reason)
				skipCSV = True

			try:
				topObj = json.loads(api.read())
				list = topObj
			except (TypeError, ValueError):
				chatters = 0


			for x in range(0, topStrims):
				queue.put(list['streams'][x]['channel']['name'])
				print bcolors.OKGREEN + "<--- " + timeMeme() + " <" + self.name + "> (" + list['streams'][x]['channel']['name'] + "): Added to Queue)"

			time.sleep(sleepTime)


#multithreaded handler for grabbing API data
class ThreadGet(threading.Thread):
    def __init__(self, queue, name):
        threading.Thread.__init__(self)
        self.queue = queue
        self.name = name
    def run(self):
		while True:
			streamer = self.queue.get()
			skipCSV = False
			timeStamp = timeMeme()

			#endpoints
			CHATTER_ENDPOINT = "http://tmi.twitch.tv/group/user/" + streamer + "/chatters"
			VIEWER_ENDPOINT = "https://api.twitch.tv/kraken/streams/" + streamer	
			UPTIME_ENDPOINT = "https://nightdev.com/hosted/uptime.php?channel=" + streamer

			#chatter count
			try:
				responseChatter = urllib2.urlopen(CHATTER_ENDPOINT)
			except urllib2.HTTPError as e:
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): API Failed (chatters). Code " + str(e.code)
				skipCSV = True
			except urllib2.URLError as e:
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): API Failed (chatters). Code " + str(e.reason)
				skipCSV = True
 
			try:
				chatterObj = json.loads(responseChatter.read())
				chatters = chatterObj['chatter_count']
			except (TypeError, ValueError):
				chatters = 0

			#get viewer count
			try:
				responseViewer = urllib2.urlopen(VIEWER_ENDPOINT)
			except urllib2.HTTPError as e:
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): API Failed (viewers). Code " + str(e.code)
				skipCSV = True
			except urllib2.URLError as e:
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): API Failed (viewers). Code " + str(e.reason)
				skipCSV = True
 
			try:
				viewerObj = json.loads(responseViewer.read())
				viewers = viewerObj['stream']['viewers']
			except (TypeError, ValueError):
				viewers = 0

			#get stream uptime
			try:
				responseUptime = urllib2.urlopen(UPTIME_ENDPOINT)
			except urllib2.HTTPError as e:
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): Uptime Failed. Code " + str(e.code)
				skipCSV = True
			except urllib2.URLError as e:
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): Uptime Failed. Code " + str(e.reason)
				skipCSV = True
 
			try:
				uptime = (responseUptime.read())
			except (TypeError, ValueError):
				uptime = "no"

			uptime = uptime.replace("The channel is not live.", "no");
			uptime = uptime.replace(" ", "").replace(",", " ");
			uptime = uptime.replace("minutes", "m").replace("minute", "m");
			uptime = uptime.replace("hours", "h").replace("hour", "h");
			uptime = uptime.replace("days", "d").replace("day", "d");

			#update console and CSV
			if skipCSV == True:
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): incomplete data, skipping :("
			elif uptime == "no":
				with open(streamer + '.csv', 'ab') as csvfile:
					writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
					writer.writerow([timeStamp, chatters, viewers])

				print bcolors.WARNING + "---> " + timeStamp + " <" + self.name + "> (" + streamer + "): " + str(chatters) + " c, " + str(viewers) + " v"
			else:
				with open(streamer + '.csv', 'ab') as csvfile:
					writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
					writer.writerow([timeStamp, chatters, viewers, uptime])	

				print bcolors.OKGREEN + "---> " + timeStamp + " <" + self.name + "> (" + streamer + "): " + str(chatters) + " c, " + str(viewers) + " v, up " + uptime

			time.sleep(0.1)
			self.queue.task_done()

def main():
	#spawn fetcher
	t = StreamerGet("00")
	t.setDaemon(False)
	t.start()

	#spawn grabbers
	for i in range(threadCount):
		t = ThreadGet(queue, str(i + 1).zfill(2))
		t.setDaemon(False)
		t.start()

	queue.join()

main()
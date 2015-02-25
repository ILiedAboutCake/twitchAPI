#Requires https://github.com/adoxa/ansicon to run on windows cmd (cleanly) -ILiedAboutCake 2015.
#also needs requests library on windows, get it with "python -m pip install -U requests"
import threading
import requests
import Queue
import json
import time
import csv

threadCount = 15 #define threads as a static number or use, len(strims) to run each as a thread. 
sleepTime = 60 #define time to reload the queue
topStrims = 25 #top number of twitch users to track
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
			    api = requests.get(endpoint + '?limit=' + str(topStrims))
			except (requests.ConnectionError, requests.ChunkedEncodingError):
			    print 'error: twitch.tv more dead than SC2'

			list = api.json()

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

			#gets chatter count
			try:
				responseChatter = requests.get(CHATTER_ENDPOINT)
			except (requests.ConnectionError, requests.ChunkedEncodingError):
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): API Failed (chatters: reset/refused)"
				skipCSV = True

			if responseChatter.status_code != requests.codes.ok:
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): API Failed (chatters). Code " + str(responseChatter.status_code)
				skipCSV = True

			try:
				chatterObj = responseChatter.json()
				chatters = chatterObj['chatter_count']
			except (TypeError, ValueError, KeyError):
				chatters = 0

			#get viewer count
			try:
				responseViewer = requests.get(VIEWER_ENDPOINT)
			except (requests.ConnectionError, requests.ChunkedEncodingError):
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): API Failed (viewers: reset/refused)"
				skipCSV = True

			if responseViewer.status_code != requests.codes.ok:
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): API Failed (viewers). Code " + str(responseViewer.status_code)
				skipCSV = True

			try:
				viewerObj = responseViewer.json()
				viewers = viewerObj['stream']['viewers']
			except (TypeError, ValueError, KeyError):
				viewers = 0

			#get stream uptime
			responseUptime = requests.get(UPTIME_ENDPOINT)

			if responseUptime.status_code != requests.codes.ok:
				print bcolors.FAIL + "<--- " + timeStamp + " <" + self.name + "> (" + streamer + "): Uptime Failed. Code " + str(responseUptime.status_code)
				skipCSV = True

			uptime = responseUptime.text
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
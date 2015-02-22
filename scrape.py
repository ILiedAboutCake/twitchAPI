#Requires https://github.com/adoxa/ansicon to run on windows cmd (cleanly) -ILiedAboutCake 2015.
#also needs requests library on windows, get it with "python -m pip install -U requests"
import threading
import requests
import Queue
import time
import csv
 
strims = ['destiny', 'nathanias', 'nl_kripp', 'phantoml0rd', 'lethalfrag', 'totalbiscuit', 'sodapoppin', 'kaceytron','timthetatman',
		'trick2g', 'piglet', 'saintvicious', 'riotgames', 'imaqtpie', 'tsm_theoddone', 'voyboy', 'aphromoo','kaylovespie','pcmtournies',
		'forsenlol', 'swiftor', 'itmejp', 'arteezy', 'summit1g', 'dendi', 'aimostfamous','twitch','trumpsc','lolpoli','spectatefaker',
		'tayzondaygames', 'dansgaming', 'goldglove', 'uknighted', 'defrancogames', 'nvidia', 'reckful', 'reynad27','towelliee','saltyteemo',
		'dinglederper', 'itshafu', 'alinity',  'legendarylea', 'livibee', 'kaitlyn', 'tigerlily___', 'alisha12287','lirik','sheebslol',
		'wintergaming', 'naniwasc2', 'basetradetv', 'gsl', 'avilo', 'taketv', 'desrowfighting', 'egjd','kristiplays','wcs','2mgovercsquared',
		'crank', 'wcs_america', 'wcs_europe', 'eghuk', 'rotterdam08', 'rootcatz', 'incontroltv', 'dragon','lagtvmaximusblack','streamerhouse',
		'dotademon','starladder3','athenelive','forsenlol','gretorptv','bacon_donut','ellohime','cdewx','monstercat','machinima','cro_',
		'kneecoleslaw','theoriginalweed','kylelandrypiano','meclipse','taymoo','watchmeblink1','steel_tv','kolento','tarik_tv','sacriel',
		'richardlewisreports', 'twitchplayspokemon', 'day9tv', 'lycangtv', 'followgrubby', 'deadmau5', 'riotgames','riotgames2']

threadCount = 15 #define threads as a static number or use, len(strims) to run each as a thread. DO NOT DO THIS UNLESS YOU WANT TO GET BANNED FROM TWITCH
sleepTime = 60 #define time to reload the queue

#start up the queue
queue = Queue.Queue()

#sets colored console stuffs
class bcolors:
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'

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

			#endpoints
			CHATTER_ENDPOINT = "http://tmi.twitch.tv/group/user/" + streamer + "/chatters"
			VIEWER_ENDPOINT = "https://api.twitch.tv/kraken/streams/" + streamer	
			UPTIME_ENDPOINT = "https://nightdev.com/hosted/uptime.php?channel=" + streamer

			#Timestamp
			timeStamp = time.strftime("%d/%m/%y %H:%M:%S", time.localtime())

			#gets chatter count
			try:
				responseChatter = requests.get(CHATTER_ENDPOINT)
			except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError):
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
			except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError):
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
	for i in range(threadCount):
		t = ThreadGet(queue, str(i + 1).zfill(2))
		t.setDaemon(False)
		t.start()

	while True:
		print bcolors.WARNING + "<--- Reloading " + str(len(strims)) + " items into queue, " + str(threading.activeCount()-1) + " Threads currently alive!"
		for streamer in strims:
			queue.put(streamer)
		time.sleep(sleepTime)
   
	queue.join()

main()
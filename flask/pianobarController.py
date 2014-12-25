import subprocess
import time

class PianobarController():
    def __init__(self):
        self.volume = 5
        self.check_status()
        self.writer = open("/root/.config/pianobar/ctl", "a")
        self.latest = ""
        self.paused = False

    def check_status(self):
        try:
            subprocess.check_call(['ps', '-C', 'pianobar'])
        except subprocess.CalledProcessError:
            #Pianobar is not running
            self.volume = 5
            self.paused = False
            self.elapsedTime = 0
            self.startTime = time.time()
            subprocess.Popen(['pianobar'])

    def pause(self):
        self.paused = not self.paused
        if self.paused:
            self.elapsedTime = self.elapsedTime + time.time() - self.startTime
        else:
            self.startTime = time.time()

    def is_paused(self):
        return self.paused

    def get_time(self):
        if self.paused:
            return self.elapsedTime
        else:
            return self.elapsedTime + time.time() - self.startTime

    def set_latest(self, action, data):
        if action == "songstart":
            self.elapsedTime = 0
            self.startTime = time.time()
        self.latest = data

    def get_latest(self):
        return self.latest

    def write(self, message):
        self.writer.write(message)
        self.writer.flush()

    def set_volume(self, volume):
        difference = abs(volume - self.volume)
        char = "("
        if volume > self.volume:
            char = ")"
        message = char * difference
        self.write(message)
        self.volume = volume

    def get_volume(self):
        return self.volume


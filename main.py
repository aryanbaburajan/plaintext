import sys
from browser import *


if __name__ == "__main__":
    browser = Browser()
    # browser.load(sys.argv[1])
    # browser.load("lol")
    # browser.load("about:blank")
    # browser.load("http://browser.engineering/examples/example1-simple.html")
    # browser.load("https://browser.engineering/examples/xiyouji.html")
    # browser.load("view-source:http://browser.engineering/examples/example1-simple.html")
    # browser.load("http://browser.engineering/examples/example1-simple.html")
    # browser.load("file:///home/aryanbaburajan/Dev/browser/main.py")
    # browser.load("data:text/plain;base64,SGVsbG8sIFdvcmxkIQ==")
    # browser.load(
    #     "data:text/html,Mixed <big>big</big> and <small>small</small>")
    browser.load("https://browser.engineering/text.html")
    # browser.load("https://paulgraham.com/google.html")
    # browser.load("https://google.com")
    tkinter.mainloop()
    browser.close()

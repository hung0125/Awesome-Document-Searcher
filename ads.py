#GUI (sudo): cd ~/ && echo "xfce4-session" > .xsession && apt install xrdp xfce4 -y --> choose lightdm
#Start GUI: service xrdp start
#Config port: nano /etc/xrdp/xrdp.ini --> set port to 3390
#Configs for GUI: apt install okular firefox
#setup (sudo): apt-get update && apt-get install python3 python3-pip tesseract-ocr -y && pip3 install testresources textract

import textract
from glob import glob
from shutil import copyfile as cpf
from math import floor
from multiprocessing import Lock, Process
from os import walk, path, cpu_count, mkdir, remove

#separate with comma, lowercase only
#keyword = "password,pwd,email,username,@gmail.com,@yahoo.com,@hotmail.com,account,帳,密碼" #Account credentials, emails
#keyword = "credit card,visa,mastercard,master card,union pay,hsbc,bank" #credit card info
keyword = "anything" #custom

source = [y for x in walk("file") for y in glob(path.join(x[0], '*.*'))]
threadNum = min(len(source), cpu_count())
mutex = Lock()
threads = []
breadth = 0
open("temp_result", "w").write("")
open("result.html", "w").write("<html><body>Put this file next to 'file' folder to make hotlinking works<br><br>")

def handleDOC(tid, word, start, pLength):
    #print(f"I handle {pLength} files, start from index {start} - {start+pLength-1}")
    
    c = 1
    for i in range(start, start + pLength):
        print(f"TID-{tid}: {i + 1}/{start + pLength} ({floor((c/pLength)*100)}%)")
        PATH = source[i].replace("\\", "/")
        wordLs = word.split(",")
        wordFound = ""
        
        cont = ""
        try:
            cont = textract.process(PATH).decode("utf-8").lower()
            #cont = str(open(PATH, "rb").read())
        except:
            pass

        for j in range(len(wordLs)):
            if wordLs[j] in cont:
                wordFound += wordLs[j] + ","

        countRes = str(wordFound.count(","))

        #accessing and writing global variable! With "try" prevents deadlock on error.
        with mutex:
            if len(wordFound) > 0:
                open("temp_result","a").write(f"{countRes}_P=<a href='{PATH}' target='_blank'>{PATH}</a>: {wordFound}<br>\n")
        
        c += 1

#main section
if __name__ == "__main__":
    print("Caution! High CPU usage!\n"*10)
    for i in range(threadNum):
        startIndex = floor(len(source)/threadNum) * i #where to start processing
        processLength = floor(len(source)/threadNum) #how many files to deal with
        if i == threadNum - 1:
            processLength = len(source) - startIndex
        try:
            threads.append(Process(target = handleDOC, args = (i+1, keyword, startIndex, processLength,)))
            threads[i].start()
        except Exception as e:
            print(e)

    for i in range(threadNum):
        threads[i].join()

    t_result = open("temp_result", "r").read().split("\n")

    for i in range(len(t_result) - 1):
        bValue =  int(t_result[i].split("_")[0])
        breadth = max(breadth, bValue)

    for i in range(breadth, 0, -1):
        for j in range(len(t_result) - 1):
            if int(t_result[j].split("_")[0]) == i:
                open("result.html", "a").write(f"{t_result[j]}\n")
                
    open("result.html", "a").write("</body></html>")
    remove("temp_result")


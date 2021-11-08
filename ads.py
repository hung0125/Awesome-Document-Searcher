import textract
from glob import glob
from shutil import copyfile as cpf
from math import floor, ceil
from multiprocessing import Lock, Process
from os import walk, path, cpu_count, remove, environ

#separate with comma, lowercase only
keyword = "password,pwd,email,username,@gmail.com,@yahoo.com,@hotmail.com,account,帳,密碼" #Account credentials, emails
#keyword = "credit card,visa,mastercard,master card,union pay,hsbc,bank" #credit card info
#keyword = "anything" #custom

source = [y for x in walk("file") for y in glob(path.join(x[0], '*.*'))] #modify target path here
mutex = Lock()
breadth = 0
environ['OMP_THREAD_LIMIT'] = '1'
open("temp_result", "w").write("")
open("result.html", "w").write("<html><body>Put this file next to 'file' folder to make hotlinking works<br><br>")

def handleDOC(tid, word, partLS):
    #print(f"I handle {len(partLS)} files, start from index {start} - {start+pLength-1}")
    
    c = 1
    for i in range(len(partLS)):
        print(f"TID-{tid}: {i + 1}/{len(partLS)} ({floor(((i + 1)/len(partLS))*100)}%)")
        c += 1

        PATH = partLS[i].replace("\\", "/")
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
                

def getSortedSrc(): #[[[..],[..]],[[..],[..]]]
    sortedSrc = []
    allExt = []
    
    #get all extensions
    for i in range(len(source)):
        ext = source[i].split(".")[len(source[i].split(".")) - 1]
        if not ext in allExt:
            allExt.append(ext)

    #divide files by extensions and do grouping for each file groups
    part = 0
    for i in range(len(allExt)):
        ext = allExt[i]
        sortedSrc.append([])
        for j in range(len(source)):
            extF = source[j].split(".")[len(source[j].split(".")) - 1]
            if extF == ext:
                sortedSrc[part].append(source[j])
        #grouping
        ls = sortFilesBySize(sortedSrc[part]) #[[a,b,c,d]]
        newls = [] #[[[a,b],[c,d]]]
        sizeCeil = 0
        for j in range(len(ls)):
            sizeCeil += path.getsize(ls[j])
        procNum = min(len(ls), cpu_count())
        sizeCeil = sizeCeil/procNum
        
        lastInd = 0
        for j in range(procNum):
            k = lastInd
            sum = 0
            templs = []
            while k < len(ls) and sum <= sizeCeil:
                templs.append(ls[k])
                sum += path.getsize(ls[k])
                k += 1
            newls.append(templs)
            lastInd = k

        sortedSrc.pop()
        sortedSrc.append(newls)

        part += 1
                
    return sortedSrc

def sortFilesBySize(ls): #to make files more evenly distributed in each processes
    temp = ls
    res = []
    sizes = []

    for i in range(len(temp)):
        sizes.append(path.getsize(temp[i]))

    sizes.sort(reverse=True)

    for i in range(len(sizes)):
        for j in range(len(temp)):
            if path.getsize(temp[j]) == sizes[i]:
                res.append(temp.pop(j))
                break
    return res
#main section
if __name__ == "__main__":
    print("Caution! High CPU usage!\n"*10)

    srtSrc = getSortedSrc()
    
    for i in range(len(srtSrc)): #[[a],[b]]
        print(f"phase {i+1} search:")
        procs = []
        for j in range(len(srtSrc[i])): 
            if len(srtSrc[i][j]) > 0:
                procs.append(Process(target = handleDOC, args = (j+1, keyword, srtSrc[i][j])))
                procs[len(procs) - 1].start()

        for j in range(len(procs)):
            procs[j].join()
            

    #Result generation
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

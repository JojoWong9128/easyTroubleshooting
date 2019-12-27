#coding=utf-8

import os
import re
import shutil
import numpy as np
import tifffile as tiff
import cv2
import matplotlib.pyplot as plt
import sys, getopt,time
import threading
import xlsxwriter

from PIL import Image
from tqdm import tqdm
from scipy import sparse
from time import ctime,sleep



#------------ version description -----------------------#

prog_version = '0.1.3'
prog_date = '2019-10-25'

#--------------       USAGE       -----------------------#
USAGE = '''
    This is an easy-troubleshooting tool of basecall on python 3. Any question, please do not hesitate to contact with Yujiao Wang<wangyujiao@genomics.cn>\r\n

        VERSION : %s by Yujiao Wang %s

        USAGE   : %s <Diagnosis Image Directory> [options]
''' % (prog_version, prog_date, os.path.basename(sys.argv[0]))


# multi-thread
exitFlag = 0
threadLock = threading.Lock()
threads = []


class myThread(threading.Thread):
    def __init__(self,threadID,name,counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        print("开始线程："+self.name)
        threadLock.acquire()
        print_time(self.name,self.counter,5)
        print("退出线程："+self.name)
        threadLock.release()


def print_time(threadName,delay,counter):
    while counter:
        if exitFlag:
            threadName.exit()
        time.sleep(delay)
        print("%s:%s"%(threadName,time.ctime(time.time())))
        counter -= 1

def _data_to_excel(arrayData, file_name, sheet = 'sheet1', output_dir = None):

    # file preparation
    full_name = file_name + '.xlsx'
    if output_dir == 'None':
        output_dir = os.getcwd()  # get the location where the command is executed

    #if output_dir == 'None':
    #    output_dir = sys.path[0]  # get python file location

    file_dir = output_dir + '\\'+full_name
    _create_file(file_dir)
    workbook = xlsxwriter.Workbook(file_dir)
    sheet_name = sheet
    worksheet = workbook.add_worksheet(sheet_name)

    # save data to Excel
    col = np.size(arrayData, 1)
    row = int(np.size(arrayData)/col)
    title_format = workbook.add_format({'bold':True,'align':'center','font':'Times New Roman'})
    data_format = workbook.add_format({'align':'center','font':'Times New Roman'})
    worksheet.write_string('A1','Cycle ID', title_format)
    worksheet.write_string('B1','Image Number', title_format)
    for rowId in range(row):
        for colId in range(col):
            worksheet.write_number(rowId+1,colId,arrayData[rowId,colId],data_format)

    workbook.close()
    print("Data has been saved in " + output_dir + " successfully.")


def _get_file_list(fileDir, fileFormat):
    fileList = []
    for root, dirs, files in os.walk(fileDir):
        for file in files:
            if os.path.splitext(file)[1] == fileFormat:
                fileList.append(file)
    return fileList


def _create_folder(folderPath):
    if os.path.exists(folderPath) & os.path.isdir(folderPath):
        shutil.rmtree(folderPath)
        os.mkdir(folderPath)
    else:
        try:
            os.mkdir(folderPath)
        except Exception as e:
            os.makedirs(folderPath)


def _create_file(fileNameWithDir, recreateFlag='true'):

    if recreateFlag:
        if os.path.isfile(fileNameWithDir):
            os.remove(fileNameWithDir)


def _get_fov_id(fileNames, outputFolder):
    maxRow = 0
    maxCol = 0

    for fileName in fileNames:
        fovId = re.findall(r"C\d\d\d"+"R\d\d\d", fileName)
        row = int(fovId[0][fovId[0].index("R")+1: fovId[0].index("R")+1+3])
        col = int(fovId[0][fovId[0].index("C")+1: fovId[0].index("C")+1+3])
        if row > maxRow:
            maxRow = row
        if col > maxCol:
            maxCol = col

    fovStatistics = sparse.dok_matrix((maxCol, maxRow))
    rowVec = np.zeros((maxRow, 1))
    colVec = np.zeros((maxCol, 1))

    for fileName in fileNames:
        fovId = re.findall(r"C\d\d\d"+"R\d\d\d", fileName)
        row = int(fovId[0][fovId[0].index("R")+1: fovId[0].index("R")+1+3])
        col = int(fovId[0][fovId[0].index("C")+1: fovId[0].index("C")+1+3])
        rowVec[row-1] = row
        colVec[col-1] = col
        fovStatistics[col-1, row-1] += 1

    fovNum  = 0
    maxFovNum = 0
    maxFovIdC = 0
    maxFovIdR = 0
    for rowId in range(0, maxRow):
        for colId in range(0, maxCol):
            if fovStatistics[colId, rowId] != 0:
                fovNum += 1
                if fovStatistics[colId, rowId] > maxFovNum:
                    maxFovNum = fovStatistics[colId, rowId]
                    maxFovIdR = rowId+1
                    maxFovIdC = colId+1

    #plt.figure("fov ID")
    plt.matshow(fovStatistics.todense())
    #plt.title("FOV ID")
    plt.text(3, -maxFovIdC/2 - 4, "total failure FOV number: "+np.str(fovNum))
    plt.text(3, -maxFovIdC/2 - 3, "C"+np.str(int(maxFovIdC))+" R"+np.str(int(maxFovIdR)) +" with largest failure image number : "+np.str(int(maxFovNum)))
    #plt.xticks(rowVec, color='black', rotation=0)
    #plt.yticks(colVec, color='black', rotation=0)
    plt.xlabel("row")
    plt.ylabel("col")
    plt.colormaps()
    plt.colorbar()
    plt.savefig(outputFolder + '/'+"fovStatistics.png")
    plt.show()
    plt.close()

    return fovStatistics


def _get_cycle_id(fileNames, outputFolder):

    minCycle = 1e4
    maxCycle = 0

    for fileName in fileNames:
        cycleMarker = re.findall(r"S\d\d\d", fileName)
        cycle = int(cycleMarker[0][cycleMarker[0].index("S")+1:cycleMarker[0].index("S")+1+3])
        if cycle < minCycle:
            minCycle = cycle
        if cycle > maxCycle:
            maxCycle = cycle
    cycleStatistics = np.zeros((maxCycle-minCycle+1, 2))
    #cycleID = np.zeros((maxCycle-minCycle+1))
    #cycleFovNum = np.zeros((maxCycle-minCycle+1))

    for fileName in fileNames:
        cycleMarker = re.findall(r"S\d\d\d", fileName)
        cycle = int(cycleMarker[0][cycleMarker[0].index("S")+1:cycleMarker[0].index("S")+1+3])
        cycleStatistics[cycle-minCycle, 0] = cycle
        cycleStatistics[cycle-minCycle, 1] += 1

    cycleNum = 0
    maxFovNum = 0
    for cycleNo in range(0, cycleStatistics[:, 0].size):
        if cycleStatistics[cycleNo, 0] != 0:
            cycleNum += 1
        if cycleStatistics[cycleNo, 1] > maxFovNum:
            maxFovNum = cycleStatistics[cycleNo, 1]
            maxFovCycleID = cycleStatistics[cycleNo, 0]

    plt.bar(cycleStatistics[:, 0], cycleStatistics[:, 1], 2, color="DarkBlue")
    #plt.xticks(cycleStatistics[:, 0], color='black', rotation=60)
    #plt.yticks(cycleStatistics[:, 1], color='black', rotation=0)
    plt.xlabel("cycle")
    plt.ylabel("image number")
    #plt.title("cycle ID")
    plt.text(0, maxFovNum+maxFovNum*0.15, "total failure cycle number: "+np.str(cycleNum))
    plt.text(0, maxFovNum+maxFovNum*0.1, "S"+np.str(int(maxFovCycleID))+" with largest failure image number : "+np.str(int(maxFovNum)))
    plt.savefig(outputFolder + '/'+"cycleStatistics.png")
    plt.show()
    plt.close('done')

    return cycleStatistics

def main():
    import argparse

    parser = argparse.ArgumentParser(usage=USAGE)
    parser.add_argument('-v',"--version",action="version",version=prog_version)
    parser.add_argument('-e',"--enhancement",action="store_true",dest="enhancemenFlag",default="false",help="apply enhancement into images. [%(default)s]")
    parser.add_argument('-s',"--statistics",action="store_true",dest="basicStatisticsFlag",default="false",help="do basic FOV and cycle statistics. [%(default)s]")
    parser.add_argument('-d',"--defects detection",action="store_true",dest="defectDetFlag",default="false",help="detect image defects and classify them. [%(default)s]")
    parser.add_argument('-o',"--output folder",action="store",dest="outputDir",default=os.getcwd(),help="save outputs into given folder. [%(default)s]")
    para,args = parser.parse_known_args()
    if len(args)<2:
        parser.print_help()
        print('\nError: Input parameter number is not correct,please check.')
        sys.exit(1)

    imgDir = args[0]


    #imgDir = r"F:\V100010724\L01\Diagnosis\FailureImages"
    imgs = _get_file_list(imgDir, ".tif")
    imgNum = len(imgs)

    if para.basicStatisticsFlag :
        print("start doing fov and cycle statistics.")
        statisticsFileName = 'Fov Cycle Statistics'
        # do fov and cycle statistics
        statisticsFolder = outputDir + "/" + "statistics"
        _create_folder(statisticsFolder)
        # get fov ID
        fovId = _get_fov_id(imgs, statisticsFolder)
        #_data_to_excel(fovId,statisticsFileName,'fovID',outputDir)
        # get cycle ID
        cycleId = _get_cycle_id(imgs, statisticsFolder)
        try:
            _data_to_excel(cycleId,statisticsFileName,'cycleID',outputDir)
        except Exception as e:
            print(e)

    if para.enhancemenFlag :
        # do image enhancement
        folderName = "EnhancedImage"
        outputPath = outputDir+"\\"+folderName
        _create_folder(outputPath)

        with tqdm(total=imgNum,ascii=True) as pbar:
            for i in range(imgNum):

                img = tiff.imread(imgDir+"\\"+imgs[i])

                #pbar.set_description("Applying enhancement into images:{}\n".format(i+1))
                pbar.set_description("Applying enhancement into images")
                pbar.update()

                maxValue = img.max()
                minValue = img.min()
                norm = np.uint8(np.round((img-minValue)/(maxValue - minValue)*255))

                img_pil = Image.open(imgDir+"\\"+imgs[i])

                normHist = cv2.equalizeHist(norm)
                imageName = os.path.splitext(imgs[i])[0]
                outputFileName = outputPath + "\\" + imageName + ".png"
                #cv2.imwrite(outputFileName, normHist)
                cv2.imencode('.png',normHist)[1].tofile(outputFileName)

        pbar.close()


    #thread1 = myThread(1,"Thread-1",1)
    #thread2 = myThread(2,"Thread-2",2)

    #thread1.start()
    #thread2.start()

    #threads.append(thread1)
    #threads.append(thread2)

    #for t in threads:
        #t.join()
    #print("退出主线程")


if __name__ == "__main__":
    main()




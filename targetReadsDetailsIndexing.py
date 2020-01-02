import sys
import os
import getopt
import argparse
import numpy as np
import csv
import xlsxwriter
from itertools import islice
import time
from datetime import datetime
from contextlib import ContextDecorator


#------------ version description -----------------------#

prog_version = '0.1.0'
prog_date = '2019-12-27'

#--------------       USAGE       -----------------------#
USAGE = '''
    This is an query tool of which queries target reads coordinate and intermediate intensity from reads bank based on python 3. Any question, please do not hesitate to contact with Yujiao Wang<wangyujiao@genomics.cn>\r\n

        VERSION : %s by Yujiao Wang %s

        USAGE   : %s <target reads ID> <reads bank> <Channel> [optional]
''' % (prog_version, prog_date, os.path.basename(sys.argv[0]))


class timer(ContextDecorator):
    def __init__(self,name):
        self.name = name
    def __enter__(self):
        self.start = datetime.now()
    def __exit__(self, *args):
        self.end = datetime.now()
        self.elapse = (self.end-self.start).total_seconds()
        print("Processing time for {} is: {} seconds".format(self.name,self.elapse))

@timer('reads_indexing')

def reads_indexing(targetReadsId,readsBankFile,dataHeader):
    readsDataBank = open(readsBankFile)
    count = 0
    targetReadsDetails = []
    for targetReads in targetReadsId:
        for reads in islice(readsDataBank,0,None):
            currReads = reads.split('\t')
            if currReads[0] == 'Spot Id':
                continue
            if currReads[0] == 'Average':
                return targetReadsDetails
            else:
                if int(currReads[0])==targetReads:
                    targetReadsDetails.append(reads)
                    count += 1
                    break
    return targetReadsDetails

@timer('get_Coor_Col')

def get_Coor_Col(readsLocsFile, channel):
    global CoorCol
    channelCoordSymbol = 'Coord.'+'x_'+channel
    lineCount = 0
    with open(readsLocsFile,encoding='utf-8',newline='') as f:
        readsLocs = csv.reader(f,delimiter='\t')
        for readsLocsIndex in readsLocs:
            if lineCount == 0:
                CoorCol = readsLocsIndex.index(channelCoordSymbol)
                break

    return CoorCol

@timer('get_data_header')

def get_data_header(dataWithHeader):
    global dataHeader
    lineCount = 0
    with open(dataWithHeader,encoding='utf-8',newline='') as dataFile:
        data = csv.reader(dataFile,delimiter='\t')
        for line in data:
            if lineCount == 0:
                dataHeader = line
                break
    return dataHeader

@timer('get_reads_coord')
def get_reads_coord(readsBankFile,channel,dataHeader,targetReadsId):
    channelCoordSymbol = 'Coord.'+'x_'+channel
    CoorCol_x = dataHeader.index(channelCoordSymbol)
    CoorCol_y = CoorCol_x + 1
    count = 0

    readsDataBank = open(readsBankFile)
    count = 0
    targetReadsLocs = np.zeros([targetReadsId.__len__(),2],np.float)
    for targetReads in targetReadsId:
        for reads in islice(readsDataBank,0,None):
            currReads = reads.split('\t')
            if currReads[0] == 'Spot Id':
                continue
            if currReads[0] == 'Average':
                return targetReadsLocs
            else:
                if int(currReads[0])==targetReads:
                    targetReadsLocs[count,0] = currReads[CoorCol_x]
                    targetReadsLocs[count,1] = currReads[CoorCol_y]
                    count += 1
                    break

    return targetReadsLocs

@timer('get_reads_ints')
def get_reads_ints(readsLocsFile,readsID,dataHeader,intermediateSymbol):
    intermediateSymbol = intermediateSymbol + '_A'
    interInt_A = dataHeader.index(intermediateSymbol)
    interInt_C = interInt_A + 1
    interInt_G = interInt_A + 2
    interInt_T = interInt_A + 3
    readsInterInts = np.genfromtxt(readsLocsFile,delimiter="\t",skip_header=1,skip_footer=4,usecols=(0,interInt_A,interInt_C,interInt_G,interInt_T))
    targetReadsInts = np.zeros([readsID.__len__(),4],np.float)
    count = 0

    for readsIndex in readsID:
        currIndexTuple = np.where(readsInterInts[:,0]==readsIndex)
        currIndex = int(currIndexTuple[0])
        targetReadsInts[count,0] = readsInterInts[currIndex,1]
        targetReadsInts[count,1] = readsInterInts[currIndex,2]
        targetReadsInts[count,2] = readsInterInts[currIndex,3]
        targetReadsInts[count,3] = readsInterInts[currIndex,4]
        count+=1
    return targetReadsInts


#@timer('save_to_txt')
def save_to_txt(data,fileName,fileFormat,outpuDir):
    fileNameWithFormat = fileName + '.'+fileFormat
    fileWithPath = outpuDir+fileNameWithFormat
    file = open(fileWithPath,'a')
    for row in data:
        for col in row:
            file.write(str(col))
            file.write(' ')
        file.write('\n')

    file.close()
    print('Data has been saved successfully.')


def getChar(number):
    factor,moder = divmod(number,26)
    modChar = chr(moder+65)
    if factor != 0:
        modChar = getChar(factor-1)+modChar
    return modChar

def save_to_excel(Data, file_name, header = None, sheet = 'sheet1', output_dir = None):

    # file preparation
    full_name = file_name + '.xlsx'
    if output_dir == 'None':
        output_dir = os.getcwd()  # get the location where the command is executed

    #if output_dir == 'None':
    #    output_dir = sys.path[0]  # get python file location

    file_dir = output_dir + full_name
    create_file(file_dir)
    workbook = xlsxwriter.Workbook(file_dir)
    sheet_name = sheet
    worksheet = workbook.add_worksheet(sheet_name)

    # save data to Excel
    title_format = workbook.add_format({'bold':True,'align':'center','font':'Times New Roman'})
    data_format = workbook.add_format({'align':'center','font':'Times New Roman'})
    count = 0
    if header != 'None':
        for headerI in header:
            char = getChar(count)
            Locs = char + '1'
            worksheet.write_string(Locs,headerI, title_format)
            count += 1

    rowId = 0
    for row in Data:
        rowId += 1
        currentRow = row.split('\t')
        col = len(currentRow)
        for colId in range(col):
            worksheet.write_string(rowId,colId,currentRow[colId],data_format)

    workbook.close()
    print("Data has been saved in " + output_dir + " successfully.")


def create_file(fileNameWithDir, recreateFlag='true'):

    if recreateFlag:
        if os.path.isfile(fileNameWithDir):
            os.remove(fileNameWithDir)

def main():
    parser = argparse.ArgumentParser(usage=USAGE)
    parser.add_argument('-v','--version',action="version",version = prog_version)
    parser.add_argument('-a','--save all details',action='store_true',dest ='saveAllDetails',default=False,help="save all details of target reads [%(default)s]")
    parser.add_argument('-o','--output dir',action='store',dest = 'outputDir',default = os.getcwd() + '\\',help='save outputs into given folder [%(default)s]')

    (para, args) = parser.parse_known_args()
    if len(args) < 3:
        parser.print_help()
        sys.exit(1)


    readsIdFile = args[0]
    readsLocsFile = args[1]
    Channel = args[2].upper()

    readsID = np.genfromtxt(readsIdFile,delimiter="\t")
    dataHeader = get_data_header(readsLocsFile)
    targetReadsLocs = get_reads_coord(readsLocsFile,Channel,dataHeader,readsID)

    if para.saveAllDetails:
        targetReadsDetails = reads_indexing(readsID,readsLocsFile,dataHeader)
        save_to_excel(targetReadsDetails,'targetReadsDetails',dataHeader,'sheet1',para.outputDir)

    #save_to_txt(targetReadsLocs,'targetReadsLocs','txt',para.outputDir)


if __name__ == '__main__':
    main()


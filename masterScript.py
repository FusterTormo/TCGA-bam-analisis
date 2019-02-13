import sqlite3
import sys
import subprocess
import GUImasterScript
import os
import shutil
import re
from datetime import datetime
import time
import multiprocessing

#Constants
pathDb = "/g/strcombio/fsupek_cancer2/TCGA_bam/info/info.db" #Absolute path where DB is stored
absHNSC = "/g/strcombio/fsupek_cancer1/TCGA_bam/" #Absolute path where HNSC and LIHC samples are stored
absLUAD = "/g/strcombio/fsupek_cancer2/TCGA_bam/" #Absolute path where LUAD, LUSC, OV and STAD samples are stored
absOthers = "/g/strcombio/fsupek_cancer3/TCGA_bam/" #Absolute path where other samples are stored
testSamps = 1

def storeDBanalysis(uuid, program, com, stlog, errlog, exitCode) :
    '''
    Inserts in the database a line with the analysis that has called this function (namely run[Strelka, Platypus, CNVkit, EXCAVATOR2,...]). In case of error during the query execution, prints the error to the console.
    The function needs all the columns of analysis table passed as parameter but the date. Namely:
    @param uuid String Unique identifyer of the bam where the analysis has been executer. Foreign key related with the sample table.
    @param program String with the name of the program that has been executed
    @param com String Complete bash command that has been executed
    @param stLog String Absolute path where the standard log has been stored in the hard drive
    @param erLog String Absolute path where the error log has been stored in the hard drive
    @param exitCode Integer Number returned as exit code by bash script (0 means exit successfully, >=1 means any type of error during execution)
    '''
    data = str(datetime.now())
    query = "INSERT INTO analysis(program, command, stLog, errorLog, date, exitCode, uuid) VALUES('{}', \"{}\", '{}', '{}', '{}', {}, '{}')".format(program, com, stlog, errlog, data, exitCode, uuid)
    con = sqlite3.connect(pathDb)
    with con :
        c = con.cursor()
        try :
            c.execute(query)
        except sqlite3.OperationalError, e :
            print "ERROR: Found error while executing query on SQLITE3.\n\tQuery executed\n\t{}\n\tDescription\n\t{}".format(query, e)

def getFolder(bam) :
    '''
    Given an absolute path where the bam file is stored, remove the name of the bam in order to get the parent folder
    @param bam absolute path where is the bam file
    '''
    aux = bam.split("/")
    return '/'.join(aux[:-1])

def deleteBam(path) :
    '''
    Removes the bam file passed as parameter from the HD. Updates the database, changing the 'deleted' column to Yes
    @param path absolute path of the bam that is going to be removed
    '''
    print "INFO: Deleting the bam {}".format(p)
    uuid = path.split("/")[-2]
    try :
        os.remove(path)
        query = "UPDATE sample SET deleted='Yes' WHERE uuid='{}'".format(uuid)
        con = sqlite3.connect(pathDb)
        with con :
            c = con.cursor()
            c.execute(query)
    except OSError, e :
        print "ERROR: Unable to delete {}.\n\tDescription:\n\t{}".format(p, e)
    except sqlite3.OperationalError, e :
        print "ERROR: Found error while executing query on SQLITE3.\n\tQuery executed\n\t{}\n\tDescription\n\t{}".format(query, e)

def getPair(bam) :
    '''
    Given an absolute path form bam file, find the pair (tumor or normal) in order to do paired analysis with them.
    To do that, first it looks at the database if the bam is tumor or normal. Then it searches for the corresponding tumor (if the bam is normal), or normal (if the bam is tumor). Finally it creates a folder in the submitter_id folder with the format UUIDtm_VS_UUIDnm
    ("First UUID from tumor"_VS_"First UUID from normal").
    If the folder exists, meaning the analysis has been done, or there is no pair in the database it will return None
    If the folder does not exist and there is a matching pair, it returns a dictionary with the keys "normal" for the absolute path for the normal sample, "tumor" for the absolute path for the tumor sample, and "folder" with the autoconstructed folder UUIDtm_VS_UUIDnm
    '''
    submitter = bam.split("/")[-3]
    uuid = bam.split("/")[-2]
    submitter_folder = getFolder(getFolder(bam))
    # Find in the database if the sample is tumor or normal
    query = "SELECT tumor FROM sample WHERE uuid='{}'".format(uuid)
    con = sqlite3.connect(pathDb)
    with con :
        pair = {"normal" : None, "tumor" : None, "folder" : None}
        c = con.cursor()
        c.execute(query)
        row = c.fetchone()
        if row == None :
            print "ERROR: uuid {} not found in the database".format(uuid)
        else :
            if re.search("Normal", row[0]) :
                pair["normal"] = bam
                #Sample is normal, search a tumor in the database to do the analysis
                query = "SELECT submitter, uuid, bamName FROM sample s WHERE s.submitter='{}' AND tumor LIKE '%Tumor%' AND deleted='No'".format(submitter)
                c.execute(query)
                row = c.fetchone()
                if row != None :
                    uuid2 = row[1]
                    #FOLDER FORMAT tumor_uuidVSnormal_uuid
                    analysis_folder = "{}_VS_{}".format(uuid2.split("-")[0], uuid.split("-")[0])
                    newDir = "{}/{}".format(submitter_folder, analysis_folder)
                    #If analysis has been performed, check if there is another tumor to perform the analysis
                    while os.path.isdir(newDir) :
                        row = c.fetchone()
                        if row == None :
                            break
                        else :
                            uuid2 = row[1]
                            #FOLDER FORMAT tumor_uuidVSnormal_uuid
                            analysis_folder = "{}_VS_{}".format(uuid2.split("-")[0], uuid.split("-")[0])
                            newDir = "{}/{}".format(submitter_folder, analysis_folder)


                #If there is a tumor that was not analyzed against the control, add it to the returning dictionary
                if row != None :
                    pair["tumor"] = "{}/{}/{}".format(submitter_folder, row[1], row[2])
                    pair["folder"] = newDir

            elif re.search("Tumor", row[0]) :
                pair["tumor"] = bam
                #Sample is tumor, search a normal in the database to do the analysis
                query = "SELECT submitter, uuid, bamName FROM sample s WHERE s.submitter='{}' AND tumor LIKE '%Normal%' AND deleted='No'".format(submitter)
                c.execute(query)
                row = c.fetchone()
                if row != None :
                    uuid2 = row[1]
                    analysis_folder = "{}_VS_{}".format(uuid.split("-")[0], uuid2.split("-")[0])
                    newDir = "{}/{}".format(submitter_folder, analysis_folder)

                    while os.path.isdir(newDir) :
                        row = c.fetchone()
                        if row == None :
                            break
                        else :
                            uuid2 = row[1]
                            analysis_folder = "{}_VS_{}".format(uuid.split("-")[0], uuid2.split("-")[0])
                            newDir = "{}/{}".format(submitter_folder, analysis_folder)


                if row != None :
                    pair["normal"] = "{}/{}/{}".format(submitter_folder, row[1], row[2])
                    pair["folder"] = newDir

    if pair["normal"] != None and pair["tumor"] != None and pair["folder"] != None :
        return pair
    else :
        return None

def runStrelkaGermline(p,folder) :
    '''
    Execute Strelka2 script and store the output and the log in a folder called strelkaGerm. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
    After that, store all the information about the analysis in the database
    '''
    #Constant name of the Strelka folder. This folder will be created in the path passed as parameter
    strelkaFolder = "strelkaGerm"
    dirStrelka = "{}/{}".format(folder, strelkaFolder)
    #Useful later to store the info in the database
    erLog = dirStrelka + "/error.log"
    stLog = dirStrelka + "/output.log"
    uuid = folder.split("/")[-1]

    print "INFO: Running Strelka2 germline in {}".format(folder)
    #Check if the analysis has been done before on the sample
    if os.path.isdir(dirStrelka) :
        print "WARNING: Strelka2 analysis has been done before. Not going to redo."
    else :
        com = '~/Scripts/runStrelka2.sh {} {}'.format(p,dirStrelka)
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate() #bash program output. Will be stored in log files

        if proc.returncode != 0 :
            print "WARNING: Strelka2 run with errors. Check log"
            print "\tCommand executed: {}".format(com)

        try :
            # Store the outputs in logs
            with open(erLog, "a") as fi :
                fi.write(sterr)
            with open(stLog, "a") as fi :
                fi.write(stout)
        except IOError, e :
            print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(com,e)

        storeDBanalysis(uuid, "Strelka2 germline", com, stLog, erLog, proc.returncode)

def runPlatypusGermline(p,folder) :
    '''
    Execute Platypus script and store the output and the log in a folder called platypusGerm. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
    After that, store all the information about the analysis in the database
    '''
    platypusFolder = "platypusGerm"
    dirPlatypus = "{}/{}".format(folder,platypusFolder)
    uuid = folder.split("/")[-1]
    outLog = dirPlatypus + "/output.log"
    erLog = dirPlatypus + "/error.log"
    com = "~/Scripts/runPlatypus.sh {} {}/platyGermline.vcf".format(p,folder)

    print "INFO: Running Platypus germline in {}".format(folder)
    #Check if the analysis has been done before on the sample
    if os.path.isdir(dirPlatypus) :
        print "WARNING: Platypus analysis has been done before. Not going to redo."
    else :
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate()
        if proc.returncode != 0 :
            print "WARNING: Platypus run with errors. Check log"
            print "\tCommand executed: {}".format(com)

        try :
            # Create the folder for Platypus and store them the output and the logs
            os.makedirs(dirPlatypus)
            with open(erLog, "a") as fi :
                fi.write(sterr)
            with open(outLog, "a") as fi :
                fi.write(stout)

            if proc.returncode == 0 :
                os.rename(folder + "/platyGermline.vcf", dirPlatypus + "/platyGermline.vcf") #Move the output vcf to the corresponding folder
                shutil.move("/home/ffuster/Scripts/log.txt", dirPlatypus + "/log.txt") #Move the log file created by Platypus to the corresponding folder

        except IOError, e :
            print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n{}".format(com,e)

        storeDBanalysis(uuid, "Platypus germline", com, outLog, erLog, proc.returncode)

def runCNVkit(folder) :
    '''
     Execute CNVkit script and store the output and the log files in a passed folder as parameter. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
     After that, store all the information about the analysis in the database
    '''
    print "INFO: Running CNVkit in {}".format(folder)
    erLog = folder + "/CNVkit/error.log"
    outLog = folder + "/CNVkit/output.log"
    uuid = folder.split("/")[-1]
    #Check if the analysis has been done before on the sample
    if os.path.isdir(folder + "/CNVkit") :
        print "WARNING: CNVkit analysis has been done before. Not going to redo."
    else :
        com = "~/Scripts/runCNVkit.sh {}".format(folder)
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate()
        if proc.returncode != 0 :
            print "WARNING: CNVkit run with errors. Check log"
            print "\tCommand executed: {}".format(com)

        try :
            #Store logs. Logs will contain the output from two analyses: using a flat reference and using a pool reference
            with open(erLog, "a") as fi :
                fi.write(sterr)
            with open(outLog, "a") as fi :
                fi.write(stout)
        except IOError, e :
            print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(com,e)

        storeDBanalysis(uuid, "CNVkit", com, outLog, erLog, proc.returncode)

def runEXCAVATOR2(p, folder) :
    '''
     Execute EXCAVATOR2 script and store the output and the log files in a folder passed as parameter. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
     After that, store all the information about the analysis in the database
    '''
    # get an alias for the bam that is necessary to run EXCAVATOR2 script
    alias = folder.split("/")[-2]
    uuid = folder.split("/")[-1]
    erLog = folder + "/EXCAVATOR2/error.log"
    outLog = folder + "/EXCAVATOR2/output.log"
    print "INFO: Running EXCAVATOR2 in {}".format(folder)
    #Check if the analysis has been done before on the sample
    if os.path.isdir(folder + "/EXCAVATOR2") :
        print "WARNING: EXCAVATOR2 analysis has been done before. Not going to redo."
    else :
        com = "ssh agendas '/g/strcombio/fsupek_cancer2/sc_repo/runEXCAVATOR2.sh {} {}'".format(p, alias)
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate()
        if proc.returncode !=0 :
            print "WARNING: EXCAVATOR2 run with errors. Check log"
            print "\tCommand executed: {}".format(com)

        try :
            #Store logs in EXCAVATOR2 folder
            with open(erLog, "a") as fi :
                fi.write(sterr)
            with open(outLog, "a") as fi :
                fi.write(stout)
        except IOError, e :
            print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(com,e)

        storeDBanalysis(uuid, "EXCAVATOR2", com, outLog, erLog, proc.returncode)

def runStrelka2Somatic(p, folder) :
    '''
    Execute Strelka2 script for compare tumor vs normal, and store the output and the log files in a folder called UUIDtm_VS_UUIDnm. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
    After that, store all the information about the analysis in the database
    '''
    tc = getPair(p)
    if tc != None :
        erLog = tc["folder"] + "/error.log"
        stLog = tc["folder"] + "/output.log"
        uuid = folder.split("/")[-1]
        print "INFO: Running Strelka2 comparing tumor vs normal in {}".format(folder)
        os.makedirs(tc["folder"])
        com = "~/Scripts/runStrelka2Somatic.sh {} {} {}".format(tc["normal"], tc["tumor"], tc["folder"])
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate()
        if proc.returncode != 0 :
            print "WARNING: Strelka2 somatic analysis exited with errors. Check log"
            print "\tCommand executed: {}".format(com)

        try :
            with open(erLog, "a") as fi:
                fi.write(sterr)
            with open(stLog, "a") as fi :
                fi.write(stout)
        except IOError, e :
            print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(com,e)

        storeDBanalysis(uuid, "Strelka2 tumor vs control", com, stLog, erLog, proc.returncode)

def runMsings(p, folder) :
    mSINGSfolder = "mSINGS"
    dirmSINGS = "{}/{}".format(folder,mSINGSfolder)
    uuid = folder.split("/")[-1]
    outLog = "{}/output.log".format(dirmSINGS)
    erLog = "{}/error.log".format(dirmSINGS)
    com = "~/Scripts/runMsings.sh {}".format(p)

    #Check if the folder exists
    if os.path.isdir(dirmSINGS) :
        print "WARNING: mSINGS analysis has been done before. Skipping the analysis"
    else :
        print "INFO: Running mSINGS in {}".format(folder)
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate()
        if proc.returncode != 0 :
            print "WARNING: mSINGS run with errors. Check log"
            print "\tCommand executed: {}".format(com)

        try :
            # Store the outputs in logs
            with open(erLog, "a") as fi :
                fi.write(sterr)
            with open(outLog, "a") as fi :
                fi.write(stout)
        except IOError, e :
            print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(com,e)

        storeDBanalysis(uuid, "mSINGS", com, outLog, erLog, proc.returncode)

def runMSIsensor(p, folder) :
    msisensorFolder = "_MSIsensor"
    tc = getPair(p)
    if tc != None :
        tc["folder"] += msisensorFolder #Add suffix to specify MSI analysis
        if os.path.isdir(tc["folder"]) :
            print "WARNING: MSIsensor analysis has been done before. Not going to redo"
        else :
            erLog = tc["folder"] + "/error.log"
            stLog = tc["folder"] + "/output.log"
            uuid = folder.split("/")[-1]
            print "INFO: Running MSIsensor in {}".format(folder)
            #IMPORTANT!! Just for a test, MSIsensor will run on the server
            #com = "~/Scripts/runMSIsensor.sh {} {} {}".format(tc["tumor"], tc["normal"], tc["folder"])
            com = "ssh agendas '/g/strcombio/fsupek_cancer2/sc_repo/runMSIsensor.sh {} {} {}'".format(tc["tumor"], tc["normal"], tc["folder"])
            proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stout, sterr = proc.communicate()
            if proc.returncode != 0 :
                print "WARNING: MSIsensor ran with errors. Check log"
                print "\tCommand executed: {}".format(com)

            try :
                with open(erLog, "a") as fi:
                    fi.write(sterr)
                with open(stLog, "a") as fi :
                    fi.write(stout)
            except IOError, e :
                print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(com,e)

            storeDBanalysis(uuid, "MSIsensor", com, stLog, erLog, proc.returncode)

def run(cancer,analysis,sampleType,delete,numSamples) :
    '''
    Run the analysis passed by parameter. First, getting the absolute path of all the samples that are going to be analysed. Second, calling the functions to run the corresponding analysis for each path. Each called function stores the output in the corresponding logs, and
    updates the database.
    Check output
    '''
    #Get the absolute paths for the samples and store it in a list
    paths = []
    #Information is extracted from the SQLITE3 database (path to DB stored in pathDb variable)
    con = sqlite3.connect(pathDb)
    with con :
        c = con.cursor()

        if numSamples == 'all' :
            query = "SELECT s.submitter, uuid, bamName, deleted FROM sample s, patient p WHERE s.submitter=p.submitter AND cancer='{}'".format(cancer)
        elif numSamples == 'sample' :
            query = "SELECT s.submitter, uuid, bamName, deleted FROM sample s, patient p WHERE s.submitter=p.submitter AND cancer='{}' ORDER BY RANDOM() LIMIT {}".format(cancer, testSamps)
        else :
            raise ValueError("Invalid number of samples to analyse")

        c.execute(query)
        rows = c.fetchall()
        for r in rows :
            if r[3] == 'No' : #Check if the bam is stered as deleted in the database
                if cancer == 'HNSC' or cancer == "LIHC":
                    auxP = absHNSC + cancer + "/" + r[0] + "/" + r[1] + "/" + r[2]
                elif cancer == 'LUAD' or cancer == 'LUSC' or cancer == "OV" or cancer == "STAD":
                    auxP = absLUAD + cancer + "/" + r[0] + "/" + r[1] + "/" + r[2]
                else :
                    auxP = absOthers + cancer + "/" + r[0] + "/" + r[1] + "/" + r[2]
                paths.append(auxP)
            else :
                print "WARNING: Not analysing {}. Bam file is deleted.".format(r[0] + "/" + r[1] + "/" + r[2])

    # paths should have the absolute paths to all the bam files ready to analyse

    #Do the corresponding analyses in all the absolute paths
    done = 0
    total = len(paths)
    print "INFO: {} analysis will be performed in {} samples\n".format(analysis, total)
    for p in paths :
        timeAnalyis = time.time()
        folder = getFolder(p)
        if analysis == 'Vcall' :
            runStrelkaGermline(p,folder)
            runPlatypusGermline(p,folder)
            runStrelka2Somatic(p, folder)
        elif analysis == 'CNV' :
            p1 = multiprocessing.Process(target=runCNVkit, args=(folder,))
            p1.start()
            p2 = multiprocessing.Process(target=runEXCAVATOR2, args=(p, folder))
            p2.start()
            p1.join()
            p2.join()
        elif analysis == 'both' :
            p1 = multiprocessing.Process(target=runStrelkaGermline, args=(p, folder))
            p1.start()
            p2 = multiprocessing.Process(target=runEXCAVATOR2, args=(p, folder))
            p2.start()
            p3 = multiprocessing.Process(target=runCNVkit, args=(folder,))
            p3.start()
            p1.join()
            p3.join()
            p4 = multiprocessing.Process(target=runPlatypusGermline, args=(p, folder))
            p4.start()
            p5 = multiprocessing.Process(target=runStrelka2Somatic, args=(p, folder))
            p5.start()
            p2.join()
            p4.join()
            p5.join
        elif analysis == 'msi' :
            #runMsings(p, folder)
            runMSIsensor(p, folder)
        else :
            #Run all the functions in parallel
            #IMPORTANT mSINGS analysis is disabled currently!!!
            #p1 = multiprocessing.Process(target=runMsings, args=(p,folder))
            #p1.start()
            p7 = multiprocessing.Process(target=runMSIsensor, args=(p,folder))
            p7.start()
            p2 = multiprocessing.Process(target=runEXCAVATOR2, args=(p, folder))
            p2.start()
            p4 = multiprocessing.Process(target=runStrelkaGermline, args=(p,folder))
            p4.start()
            p5 = multiprocessing.Process(target=runPlatypusGermline, args=(p,folder))
            p5.start()
            p4.join() # Wait until Strelka2 germline finishes, then run Strelka somatic, and CNVkit (as the computer will be less overloaded)
            p5.join()
            p6 = multiprocessing.Process(target=runStrelka2Somatic, args=(p,folder))
            p6.start()
            p3 = multiprocessing.Process(target=runCNVkit, args=(folder,))
            p3.start()
            #p1.join()
            p2.join()
            p3.join()
            p7.join()
            p6.join()

        done += 1
        timeElapsed = time.time() - timeAnalyis
        print "INFO: {} analysis performed. {} remaining. {:.2%} complete\n".format(done, total-done, float(done)/total)
        print "Time elapsed in this analysis: {}".format(time.strftime("%H:%M:%S", time.gmtime(timeElapsed)))
        if delete == "y" :
            deleteBam(p)

def read_params(args) :
    '''
    Check if there are unexpected parameters
    Allowed parameters are :
        [1] - Valid cancer TCGA type
        [2] - Valid type of analysis {Vcall, CNV, both, msi, all}
        [3] - If analysis will be done in {all} samples, only in {tumor}, or only in {normal}
        [4] - If bams analysed will be deleted {y, n}
        [5] - In how many samples run the analysis {sample, all}
    Regarding this last parameter, sample means a particular number of samples, taken randomly from the database
    '''
    cancer = analysis = sampleType = delete = numSamples = None

    #Check if the cancer name is valid
    con = sqlite3.connect(pathDb)
    with con :
        c = con.cursor()
        c.execute("SELECT DISTINCT cancer FROM patient")
        rows = c.fetchall()
        for r in rows :
            if sys.argv[1] in r :
                cancer = sys.argv[1]
                break

    if cancer == None :
        raise ValueError("Invalid name of cancer (param 1)")

    #Check if type of analysis is valid
    if sys.argv[2] == 'Vcall' or sys.argv[2] == 'CNV' or sys.argv[2] == 'both' or sys.argv[2] == 'msi' or sys.argv[2] == 'all':
        analysis = sys.argv[2]
    else :
        raise ValueError("Invalid option for type of analysis (param 2)")

    #Check where analyses will be done
    if sys.argv[3] == 'all' or sys.argv[3] == 'tumor' or sys.argv[3] == 'normal' :
        sampleType = sys.argv[3]
    else :
        raise ValueError("Invalid type of samples (param 3)")

    #Check if bams analysed will be deleted or not
    if sys.argv[4] == 'y' or sys.argv[4] == 'n' :
        delete = sys.argv[4]
    else :
        raise ValueError("Invalid option in param 4. This option means if bam files should be deleted or not")

    #Check in how many samples do the analyses
    if sys.argv[5] == 'sample' or sys.argv[5] == 'all' :
        numSamples = sys.argv[5]
    else :
        raise ValueError("Invalid option for number of samples to be analysed (param 5)")

    #Parameters are correct, run the analysis
    run(cancer,analysis,sampleType,delete, numSamples)

def main() :
    '''
    Checks if the users wants the GUI to customize the parameters, or wants to execute the analyses directly
    '''
    start = time.time()
    if len(sys.argv) < 6 :
        GUImasterScript.screen_Cancer()
    else :
        try :
            read_params(sys.argv)
        except ValueError, e :
            print e
            GUImasterScript.screen_Cancer()

    elapsed = time.time() - start
    print "MISSION ACCOMPLISHED. Elapsed time: {}".format(time.strftime("%H:%M:%S", time.gmtime(elapsed)))

if __name__ == "__main__":
    main()

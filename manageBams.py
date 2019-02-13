import masterScriptLib as ml
import masterScriptConstants as mc
import createBatch as cb
import checkAnalysis as ch
import checkDownloads as downloads
import tcgaAPI as tcga
import os
import shutil
import sys
import sqlite3
import time
import subprocess
import stat

'''Controls status for the TCGA using different python scripts
- masterScriptLib is used to run the analysis locally for one TCGA case
- createBatch is used to create the batch scripts to run the analyses for one complete cancer in the server
- checkAnalysis is used to look which samples are completely analysed, which bams are able to delete. Additionally, it checks if there are pending analyses, and creates the script to run the pending analyses locally.
- checkDownloads is used to compare the cancer folders and the database in order to know if there are any cancer that is fully downloaded, but not stored in the database
Opens '''

cancerPath = mc.cancerPath

def getNext(samp, cancer) :
    q = "SELECT DISTINCT p.submitter FROM patient p JOIN sample s ON s.submitter=p.submitter WHERE cancer='{}' AND deleted='No' AND p.submitter > '{}' ORDER BY p.submitter LIMIT 1".format(cancer, samp)
    db = sqlite3.connect(mc.pathDb)
    sub = None
    with db :
        try :
            cur = db.cursor()
            x = cur.execute(q)
            sub = x.fetchone()
        except sqlite3.OperationalError, e :
            print "ERROR: Error found executing {}\nDescription:\n{}".format(q,e)

    return sub[0]

def recover(samps, last, num) :
    '''Finds the last sample analysed and returns a sublist with all the pending samples. The variable samps must be sorted by
    submitter id'''
    sulist = []
    try :
        ndex = samps.index(last)
        end = int(num) + ndex
        if end < len(samps) :
            sulist = samps[ndex:end]
        else :
            sulist = samps[ndex:]
        return sulist
    except ValueError :
        print "ERROR: Submitter id not found in the list. Exiting"
        sys.exit()

def GUIselectCancer() :
    cancers = list(cancerPath.keys())
    cancers.sort()
    print "Select cancer to run: "
    print "========================================="
    print "\t".join(cancers)
    print "========================================="
    inp = raw_input("Cancer selected: ")
    opt = inp.upper()
    if opt in cancers :
        return opt
    else :
        raise ValueError("Cancer selected is not in the list")

def GUIselectAnalysis() :
    keys = list(mc.analyses.keys())
    keys.sort()
    print "Select analysis to do"
    print "========================================="
    for a in keys :
        print "[{}] - {}".format(a, mc.analyses[a])
    print "========================================="
    int = raw_input("Your choice: ")
    if int in keys :
        return int
    else :
        raise ValueError("Analysis selected is not in the list")

def GUI4stats() :
    opt = GUIselectCancer()
    ch.getStats(opt)

def doReports() :
    print "INFO: Preparing reports to all the cancers"
    for c in cancerPath :
        path = "{}/{}".format(cancerPath[c], c) #Path where the cancer data is stored. It will be used to store the report there
        print "INFO: Preparing {} report".format(c)
        #Redirect standard output to text file
        original_stout = sys.stdout
        fi = open("temp.txt", "w")
        sys.stdout = fi
        ch.getStats(c, False)
        sys.stdout = original_stout
        fi.close()
        #Parse the text file to get only the interesting information
        with open("{}/analysisStatus.txt".format(path), "w") as dest :
            with open("temp.txt", "r") as fi :
                for line in fi :
                    if line == "\n" or line.startswith("INFO:") :
                        pass
                    else :
                        dest.write(line)
        shutil.move("pending.md", "{}/pending.md".format(path))
        os.remove("temp.txt")
    print "INFO: All report status stored as analysisStatus.txt. All pending analyses stored in pending.md file in the same folder"

def GUI4batch() :
    opt = GUIselectCancer()
    cb.run(opt)

def GUI4check() :
    opt = GUIselectCancer()
    ch.checkSamples(opt, True)

def GUI4dwSample() :
    case = raw_input("Sample case ID to download (Tip: TCGA- prefix is not mandatory): ").upper()
    uuids = []
    if not case.startswith("TCGA-") :
        case = "TCGA-{}".format(case)

    #Look for the ID in the database. Get the sample full path
    q = "SELECT cancer FROM patient WHERE submitter='{}'".format(case)
    db = sqlite3.connect(mc.pathDb)
    with db :
        try :
            c = db.cursor()
            x = c.execute(q)
            xx = x.fetchone()
        except sqlite3.OperationalError, e :
            print "ERROR: Error found executing {}\nDescription:\n{}".format(q,e)

    # Check if ID exists
    if xx == None :
        raise ValueError("Case ID not found")
    else :
        cancer = str(xx[0])
        with db :
            q = "SELECT uuid FROM sample WHERE submitter='{}'".format(case)
            try :
                c = db.cursor()
                x = c.execute(q)
                xx = x.fetchall()
                for i in xx :
                    uuids.append(str(i[0]))

            except sqlite3.OperationalError, e :
                print "ERROR: Error found executing {}\nDescription:\n{}".format(q,e)


    if uuids != [] :
        # Ask for analysis to do in the sample
        anal = GUIselectAnalysis()
        cdCommand = "{}/{}/{}".format(cancerPath[cancer], cancer, case)
        auxdir = os.getcwd()
        os.chdir(cdCommand)
        print "INFO: Going to download {} bams".format(len(uuids))
        #Download the sample
        tcga.downloadSample(case)
        ar = ["masterScriptLib.py", case, anal, "yes"]
        print "INFO: Running analysis. {}\nNOTICE: Bam will be deleted after the analysis".format(ar)
        os.chdir(auxdir)
        ml.readParams(ar)
    else :
        print "ERROR: No bam uuids found in {} case".format(case)

def GUI4newCancer() :
    folderManifests = "/mnt/data/TCGA_bam" #Information extracted from tcgaAPI. If it doew not work look that the path is not changed...
    serverFolder = "/g/strcombio/fsupek_cancer3/TCGA_bam"
    getBam = "/home/ffuster/Scripts/getBams.sh"
    # Get available cancers
    avData = tcga.availableCancers()
    if avData != [] :
        print "Which cancer want to download? "
        for a in avData :
            print a
        folder = raw_input("Your option: ")
        if folder in avData :
            # Create the folder to store the manifests
            path = "{}/{}".format(folderManifests, folder)
            os.makedirs(path)
            # Run tcgaAPI to download the manifests
            tcga.getManifests(folder)
            # Copy the data to cancer3 using rsync
            command = "rsync -aP {} {}".format(path, serverFolder)
            os.system(command)
            # Create a getBams.sh and store it in cancer3 cancer folder
            path = "{}/{}".format(serverFolder, folder)
            with open(getBam, "r") as rd, open("{}/getBams.sh".format(path), "w") as wr:
                for lines in rd :
                    if lines.startswith("cd ") :
                        wr.write("cd {}\n".format(path))
                    else :
                        wr.write(lines)

            os.chmod("{}/getBams.sh".format(path), stat.S_IRWXU)
            print "INFO: Manifests stored in {}. Created a bash script to download the data".format(serverFolder)
            print "\tUsage:\n\tcd {}; ./getBams.sh".format(path)
        else :
            raise ValueError("Invalid cancer")


def GUI4local() :
    """
    (G)raphic (U)ser (I)nterface to run local analyses in TCGA bams. This function is called when the user selects option 4.
    First, gets the cancer where local analyses will be executed. To do that it calls GUIselectCancer function.
    After, asks how many samples run (1,10, 100, or all). In this moment, it is possible to ask a submitter starting point.
    Last, asks if user wants to delete the bams or not
    When all options are set, it calls masterSciptLib library to run the analyses in the list of submitters selected. If the analysis is not run in all the samples, it prints the last sample analysed, and the name of the next sample to analyse.
    """
    opt = GUIselectCancer()
    sql = raw_input("\nFolder to store the SQL insertions (enter to current folder): ")
    if sql == "" :
        sql = "."
    if os.path.isdir(sql) :
        mc.pathSql = sql + "/" + mc.pathSql
    else :
        raise ValueError("Invalid path")

    samps = raw_input("\nHow many samples you want to run? (1, 10, 100, all): ")
    delBams = False
    lastItem = ""
    if samps == "1" or samps == "10" or samps == "100" :
        samps = int(samps)
        lastItem = raw_input("\nFrom which submitter you want to start? (enter to start from the beginning): ")
        if lastItem != "" :
            aux = samps
            samps = "all"
    elif samps == "all" :
        delBams = raw_input("\nDelete the bams after successfull analysis? (y/n): ")
        if delBams == "y" :
            delBams = True
        elif delBams == "n" :
            delBams = False
        else :
            raise ValueError("Invalid option")
    else :
        raise ValueError("Not supported option")

    #Up to here, the three variables must be set: will have the cancer type, samps the number of samples to do the analysis, delBams a boolean to delete bams or not
    if samps == "all" :
        query = "SELECT DISTINCT p.submitter FROM patient p JOIN sample s ON s.submitter=p.submitter WHERE cancer='{}' AND deleted='No' ORDER BY p.submitter".format(opt)
    else :
        query = "SELECT DISTINCT p.submitter FROM patient p JOIN sample s ON s.submitter=p.submitter WHERE cancer='{}' AND deleted='No' ORDER BY p.submitter LIMIT {}".format(opt,samps)

    db = sqlite3.connect(mc.pathDb)
    with db :
        try :
            cur = db.cursor()
            x = cur.execute(query)
            submitters = []
            for a in x.fetchall() :
                submitters.append(a[0])
        except sqlite3.OperationalError, e :
            print "ERROR: Found error executing query {}\nDescription:\n{}".format(query, e)

    if lastItem != "" :
        submitters = recover(submitters, lastItem, aux)

    for s in submitters :
        if delBams :
            ar = ["masterScriptLib.py", s, "all", "yes"]
        else :
            ar = ["masterScriptLib.py", s, "all", "no"]
        st = time.time()
        ml.readParams(ar)
        elapsed = time.time() - st
        print "INFO: Time elapsed in complete analysis {}".format(time.strftime("%H:%M:%S", time.gmtime(elapsed)))

    print "INFO: Last sample analysed: {}".format(s)
    sig = getNext(s, opt)
    if sig != None :
        print "\nINFO: Next sample to analyse: {}".format(sig)

def mainGUI() :
    """
    Main (G)raphic (U)ser (I)nterface. Show all the available functions to work with TCGA bams. Each option launches different GUIs. If the user inputs a bad option, an ValueError exception is raised and the program ends
    """
    os.system("clear")
    print "\n\n\nHi! What you want?"
    print "================================================================================"
    print "\t[0] Get stats from a particular cancer"
    print "\t[1] Write report status for all downloaded cancers"
    print "\t[2] Find which bams are pending to remove & remove them"
    print "\t[3] Create batch scripts to run in the server"
    print "\t[4] Analyse one or more samples in local computer"
    print "\t[5] Check if the database is up to date regarding bam downloads"
    print "\t[6] Re-download one case to run some analyses"
    print "\t[7] Download a new cancer from TCGA"
    print "================================================================================\n"
    opt = raw_input("Your option: ")
    if opt == '0' :
        GUI4stats()
    elif opt == '1' :
        doReports()
    elif opt == '2' :
        GUI4check()
    elif opt == '3' :
        GUI4batch()
    elif opt == '4' :
        GUI4local()
    elif opt == '5' :
        downloads.main()
    elif opt == '6' :
        GUI4dwSample()
    elif opt == '7' :
        GUI4newCancer()
    else :
        raise ValueError("Invalid option: {}".format(opt))

mainGUI()

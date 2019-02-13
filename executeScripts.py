from datetime import datetime
import time
import multiprocessing
import sqlite3
import re
import os
import sys
import subprocess
import shutil
import masterScriptConstants as mc


def getFolder(bam) :
    '''
    Given an absolute path where the bam file is stored, remove the name of the bam in order to get the parent folder
    @param bam absolute path where is the bam file
    '''
    aux = bam.split("/")
    return '/'.join(aux[:-1])

def getPair(bam, program) :
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
    con = sqlite3.connect(mc.pathDb)
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
                    #FOLDER FORMAT tumorUUID_VS_normalUUID_program
                    analysis_folder = "{}_VS_{}_{}".format(uuid2.split("-")[0], uuid.split("-")[0], program)
                    newDir = "{}/{}".format(submitter_folder, analysis_folder)
                    #If analysis has been performed, check if there is another tumor to perform the analysis
                    while os.path.isdir(newDir) :
                        row = c.fetchone()
                        if row == None :
                            break
                        else :
                            uuid2 = row[1]
                            #FOLDER FORMAT tumorUUID_VS_normalUUID_program
                            analysis_folder = "{}_VS_{}_{}".format(uuid2.split("-")[0], uuid.split("-")[0], program)
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
                    analysis_folder = "{}_VS_{}_{}".format(uuid.split("-")[0], uuid2.split("-")[0], program)
                    newDir = "{}/{}".format(submitter_folder, analysis_folder)

                    while os.path.isdir(newDir) :
                        row = c.fetchone()
                        if row == None :
                            break
                        else :
                            uuid2 = row[1]
                            analysis_folder = "{}_VS_{}_{}".format(uuid.split("-")[0], uuid2.split("-")[0], program)
                            newDir = "{}/{}".format(submitter_folder, analysis_folder)


                if row != None :
                    pair["normal"] = "{}/{}/{}".format(submitter_folder, row[1], row[2])
                    pair["folder"] = newDir

    if pair["normal"] != None and pair["tumor"] != None and pair["folder"] != None :
        return pair
    else :
        return None

def registerAnalysis(uuid, program, command, stlog, erlog, exitcode, elapsed) :
    data = str(datetime.now())
    query = "INSERT INTO analysis(program, command, stLog, errorLog, date, exitCode, uuid, elapsedTime) VALUES('{}', \"{}\", '{}', '{}', '{}', {}, '{}', '{}')".format(program, command, stlog, erlog, data, exitcode, uuid, elapsed)
    with open(mc.pathSql, "a") as fi :
        fi.write("{};\n".format(query))
        print "INFO: Analysis stored in {}".format(mc.pathSql)

def runStrelka2Germline(bam,folder) :
    '''
    Execute Strelka2 script and store the output and the log in a folder called strelkaGerm. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
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
        return 0
    else :
        strt = time.time()
        com = '{}/runStrelka2.sh {} {}'.format(mc.pathScripts, bam,dirStrelka)
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate() #bash program output. Will be stored in log files

        if proc.returncode != 0 :
            print "WARNING: Strelka2 ran with errors. Check log"
            print "\tCommand executed: {}".format(com)

        try :
            # Store the outputs in logs
            with open(erLog, "a") as fi :
                fi.write(sterr)
            with open(stLog, "a") as fi :
                fi.write(stout)
        except IOError, e :
            print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(com,e)

        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "Strelka2 germline", com, stLog, erLog, proc.returncode, elapsedTime)
        return proc.returncode

def runPlatypus(bam,folder) :
    '''
    Execute Platypus script and store the output and the log in a folder called platypusGerm. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
    After that, store all the information about the analysis in the database
    '''
    platypusFolder = "platypusGerm"
    dirPlatypus = "{}/{}".format(folder,platypusFolder)
    uuid = folder.split("/")[-1]
    outLog = dirPlatypus + "/output.log"
    erLog = dirPlatypus + "/error.log"
    com = "{}/runPlatypus.sh {} {}/platyGermline.vcf".format(mc.pathScripts, bam,folder)

    print "INFO: Running Platypus germline in {}".format(folder)
    #Check if the analysis has been done before on the sample
    if os.path.isdir(dirPlatypus) :
        print "WARNING: Platypus analysis has been done before. Not going to redo."
        return 0
    else :
        strt = time.time()
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
                shutil.move("{}/log.txt".format(os.getcwd()), dirPlatypus + "/log.txt") #Move the log file created by Platypus to the corresponding folder

        except IOError, e :
            print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n{}".format(com,e)

        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "Platypus germline", com, outLog, erLog, proc.returncode, elapsedTime)
        return proc.returncode

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
        return 0
    else :
        strt = time.time()
        com = "{}/runCNVkit.sh {}".format(mc.pathScripts,folder)
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

        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "CNVkit", com, outLog, erLog, proc.returncode, elapsedTime)
        return proc.returncode

def runEXCAVATOR2(bam, folder) :
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
        return 0
    else :
        strt = time.time()
        com = "{}/runEXCAVATOR2.sh {} {}".format(mc.pathScripts, bam, alias)
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

        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "EXCAVATOR2", com, outLog, erLog, proc.returncode, elapsedTime)
        return proc.returncode

def runStrelka2Somatic(bam, folder) :
    '''
    Execute Strelka2 script for compare tumor vs normal, and store the output and the log files in a folder called UUIDtm_VS_UUIDnm. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
    After that, store all the information about the analysis in the database
    '''
    tc = getPair(bam, "Strelka2")
    if tc != None :
        strt = time.time()
        erLog = tc["folder"] + "/error.log"
        stLog = tc["folder"] + "/output.log"
        uuid = folder.split("/")[-1]
        print "INFO: Running Strelka2 comparing tumor vs normal in {}".format(folder)
        os.makedirs(tc["folder"])
        com = "{}/runStrelka2Somatic.sh {} {} {}".format(mc.pathScripts, tc["normal"], tc["tumor"], tc["folder"])
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

        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "Strelka2 somatic", com, stLog, erLog, proc.returncode, elapsedTime)
        return proc.returncode
    else :
        return 0

def runMSIsensor(bam, folder) :
    tc = getPair(bam, "MSIsensor")
    exitCode = 0
    if tc != None :
        if os.path.isdir(tc["folder"]) :
            print "WARNING: MSIsensor analysis has been done before. Not going to redo"
        else :
            strt = time.time()
            erLog = tc["folder"] + "/error.log"
            stLog = tc["folder"] + "/output.log"
            uuid = folder.split("/")[-1]
            print "INFO: Running MSIsensor in {}".format(folder)
            com = "{}/runMSIsensor.sh {} {} {}".format(mc.pathScripts, tc["tumor"], tc["normal"], tc["folder"])

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

            end = time.time() - strt
            elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
            registerAnalysis(uuid, "MSIsensor", com, stLog, erLog, proc.returncode, elapsedTime)
            exitCode = proc.returncode

    return exitCode

def runMantaGermline(bam, folder) :
    '''
    Execute Manta script for germline analysis. Store the output and the logs in a folder called mantaGerm. If there are execution errors, warning messages would be printedself.
    '''
    mantaFolder = "mantaGerm"
    dirManta = "{}/{}".format(folder,mantaFolder)
    erLog = dirManta + "/error.log"
    stLog = dirManta + "/output.log"
    uuid = folder.split("/")[-1]

    print "INFO: Running Manta germline analysis in {}".format(folder)
    if os.path.isdir(dirManta) :
        print "WARNING: Manta germline has been done before. Skipping"
        return 0
    else :
        strt = time.time()
        com = "{}/runMantaGerminal.sh {} {}".format(mc.pathScripts, bam, dirManta)
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate() #bash program output. Will be stored in log files

        if proc.returncode != 0 :
            print "WARNING: Manta ran with errors. Check log"
            print "\tCommand executed: {}".format(com)

        try :
            # Store the outputs in logs
            with open(erLog, "a") as fi :
                fi.write(sterr)
            with open(stLog, "a") as fi :
                fi.write(stout)
        except IOError, e :
            print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(com,e)
        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "Manta germline", com, stLog, erLog, proc.returncode, elapsedTime)
        return proc.returncode

def runMantaSomatic(bam, folder) :
    tc = getPair(bam, "Manta")
    exitCode = 0
    if tc != None :
        if os.path.isdir(tc["folder"]) :
            print "WARNING: Manta somatic was done before. Skipping"
        else :
            strt = time.time()
            erLog = tc["folder"] + "/error.log"
            stLog = tc["folder"] + "/output.log"
            uuid = folder.split("/")[-1]
            print "INFO: Running Manta somatic analysis in {}".format(folder)
            com = "{}/runMantaSomatic.sh {} {} {}".format(mc.pathScripts, tc["normal"], tc["tumor"], tc["folder"])
            proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stout, sterr = proc.communicate() #bash program output. Will be stored in log files

            if proc.returncode != 0 :
                print "WARNING: Manta somatic ran with errors. Check log"
                print "\tCommand executed: {}".format(com)

            try :
                # Store the outputs in logs
                with open(erLog, "a") as fi :
                    fi.write(sterr)
                with open(stLog, "a") as fi :
                    fi.write(stout)
            except IOError, e :
                print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(com,e)

            end = time.time() - strt
            elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
            registerAnalysis(uuid, "Manta somatic", com, stLog, erLog, proc.returncode, elapsedTime)
            exitCode = proc.returncode
    return exitCode

def runFacets(bam, folder) :
    tc = getPair(bam, "FACETS")
    exitCode = 0
    if tc != None :
        if os.path.isdir(tc["folder"]) :
            print "WARNING: FACETS was done before. Skiping"
        else :
            strt = time.time()
            erLog = tc["folder"] + "/error.log"
            stLog = tc["folder"] + "/output.log"
            uuid = folder.split("/")[-1]
            print "INFO: Running FACETS analysis in {}".format(folder)
            com = "{}/runFacets.sh {} {} {}".format(mc.pathScripts, tc["normal"], tc["tumor"], tc["folder"])
            proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stout, sterr = proc.communicate() #bash program output. Will be stored in log files

            if proc.returncode != 0 :
                print "WARNING: FACETS ran with errors. Check log"
                print "\tCommand executed: {}".format(com)

            try :
                # Store the outputs in logs
                with open(erLog, "a") as fi :
                    fi.write(sterr)
                with open(stLog, "a") as fi :
                    fi.write(stout)
            except IOError, e :
                print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(com,e)

            end = time.time() - strt
            elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
            registerAnalysis(uuid, "FACETS", com, stLog, erLog, proc.returncode, elapsedTime)
            exitCode = proc.returncode
    return exitCode

def runAscatNgs(bam, folder, gender) :
    tc = getPair(bam, "ASCAT")
    exitCode = 0
    if tc != None :
        if os.path.isdir(tc["folder"]) :
            print "WARNING: AscatNGS was done before. Skipping"
        else :
            strt = time.time()
            erLog = tc["folder"] + "/error.log"
            stLog = tc["folder"] + "/output.log"
            uuid = folder.split("/")[-1]
            print "INFO: Running AscatNGS in {}".format(folder)
            com = "{}/runAscat.sh {} {} {} {}".format(mc.pathScripts, tc["normal"], tc["tumor"], tc["folder"], gender)
            proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stout, sterr = proc.communicate() #bash program output. Will be stored in log files

            if proc.returncode != 0 :
                print "WARNING: AscatNGS ran with errors. Check log"
                print "\tCommand executed: {}".format(com)

            try :
                # Store the outputs in logs
                with open(erLog, "a") as fi :
                    fi.write(sterr)
                with open(stLog, "a") as fi :
                    fi.write(stout)
            except IOError, e :
                print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(com,e)

            end = time.time() - strt
            elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
            registerAnalysis(uuid, "AscatNGS", com, stLog, erLog, proc.returncode, elapsedTime)
            exitCode = proc.returncode
    return exitCode

def runBedtools(bam, folder) :
    bedFolder = "genomeCoverage"
    dirBedtools = "{}/{}".format(folder, bedFolder)
    uuid = folder.split("/")[-1]
    outLog = dirBedtools + "/output.log"
    erLog = dirBedtools + "/error.log"
    print "INFO: Running bedtools genomeCoverage in {}".format(folder)
    if os.path.isdir(dirBedtools) :
        print "WARNING: Bedtools genomeCov has been done before. Skipping"
        return 0
    else :
        strt = time.time()
        com = "{}/runGenomeCov.sh {}".format(mc.pathScripts, bam)
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate()
        if proc.returncode != 0 :
            print "WARNING: Bedtools genomeCoverage ran with errors. Check log"
            print "\tCommand executed: {}".format(com)

        try :
            # Create the folder for Platypus and store them the output and the logs
            os.makedirs(dirBedtools)
            with open(erLog, "a") as fi :
                fi.write(sterr)
            with open(outLog, "a") as fi :
                fi.write(stout)

            if proc.returncode == 0 :
                shutil.move("{}/bamCoverage.tsv".format(os.getcwd()), dirBedtools + "/bamCoverage.tsv") #Move the output file to the corresponding folder

        except IOError, e :
            print "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n{}".format(com,e)

        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "Bedtools genomeCov", com, outLog, erLog, proc.returncode, elapsedTime)
        return proc.returncode

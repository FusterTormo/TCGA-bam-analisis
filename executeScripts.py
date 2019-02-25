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

pathDb = mc.pathDb
pathScripts = mc.pathScripts
pathSql = mc.pathSql
finish_file = mc.finish_file

def getFolder(bam):
    '''
    Given an absolute path where the bam file is stored, remove the name of the bam in order to get the parent folder
    @param bam absolute path where is the bam file
    '''
    aux = bam.split("/")
    return '/'.join(aux[:-1])


def getPair(bam, program):
    '''
    Given an absolute path form bam file, find the pair (tumor or normal) in order to do paired analysis with them.
    To do that, first it looks at the database if the bam is tumor or normal. Then it searches for the corresponding tumor (if the bam is normal), or normal (if the bam is tumor). Finally it creates a folder in the submitter_id folder with the format UUIDtm_VS_UUIDnm
    ("First UUID from tumor"_VS_"First UUID from normal").
    If the folder exists (and .finished has been created), meaning the analysis has been previously succesfully run, or there is no pair in the database it will return None
    If the folder does not exist, or .finished is not present and there is a matching pair, it returns a dictionary with the keys "normal" for the absolute path for the normal sample, "tumor" for the absolute path for the tumor sample, and "folder" with the autoconstructed folder UUIDtm_VS_UUIDnm
    '''
    submitter = bam.split("/")[-3]
    uuid = bam.split("/")[-2]
    submitter_folder = getFolder(getFolder(bam))
    # Find in the database if the sample is tumor or normal
    query = "SELECT tumor FROM sample WHERE uuid='{}'".format(uuid)
    con = sqlite3.connect(pathDb)
    with con:
        pair = {"normal": None, "tumor": None, "folder": None}
        c = con.cursor()
        c.execute(query)
        row = c.fetchone()
        if row == None:
            print >> sys.stderr, "ERROR: uuid {} not found in the database".format(uuid)
        else:
            if re.search("Normal", row[0]):
                pair["normal"] = bam
                # Sample is normal, search a tumor in the database to do the analysis
                query = "SELECT submitter, uuid, bamName FROM sample s WHERE s.submitter='{}' AND tumor LIKE '%Tumor%' AND deleted='No'".format(
                    submitter)
                c.execute(query)
                row = c.fetchone()
                if row != None:
                    uuid2 = row[1]

                    # FOLDER FORMAT tumor_uuidVSnormal_uuid_program
                    analysis_folder = "{}_VS_{}_{}".format(uuid2.split("-")[0], uuid.split("-")[0], program)
                    newDir = "{}/{}".format(submitter_folder, analysis_folder)
                    # If analysis has been performed, check if there is another tumor to perform the analysis
                    while os.path.isdir(newDir):
                        row = c.fetchone()
                        if row == None:
                            break
                        else:
                            uuid2 = row[1]
                            # FOLDER FORMAT tumor_uuidVSnormal_uuid
                            analysis_folder = "{}_VS_{}".format(uuid2.split("-")[0], uuid.split("-")[0])
                            newDir = "{}/{}".format(submitter_folder, analysis_folder)

                # If there is a tumor that was not analyzed against the control, add it to the returning dictionary
                if row != None:
                    pair["tumor"] = "{}/{}/{}".format(submitter_folder, row[1], row[2])
                    pair["folder"] = newDir

            elif re.search("Tumor", row[0]):
                pair["tumor"] = bam
                # Sample is tumor, search a normal in the database to do the analysis
                query = "SELECT submitter, uuid, bamName FROM sample s WHERE s.submitter='{}' AND tumor LIKE '%Normal%' AND deleted='No'".format(
                    submitter)
                c.execute(query)
                row = c.fetchone()
                if row != None:
                    uuid2 = row[1]
                    analysis_folder = "{}_VS_{}_{}".format(uuid.split("-")[0], uuid2.split("-")[0], program)
                    newDir = "{}/{}".format(submitter_folder, analysis_folder)
                    finished_before = "{}/{}".format(newDir, finish_file)

                    # while os.path.isdir(newDir) :
                    while os.path.isdir(finished_before):
                        row = c.fetchone()
                        if row == None:
                            break
                        else:
                            uuid2 = row[1]
                            analysis_folder = "{}_VS_{}".format(uuid.split("-")[0], uuid2.split("-")[0])
                            newDir = "{}/{}".format(submitter_folder, analysis_folder)

                if row != None:
                    pair["normal"] = "{}/{}/{}".format(submitter_folder, row[1], row[2])
                    pair["folder"] = newDir

    if pair["normal"] != None and pair["tumor"] != None and pair["folder"] != None:
        return pair
    else:
        return None


def registerAnalysis(uuid, program, command, stlog, erlog, exitcode, elapsed):
    data = str(datetime.now())
    query = "INSERT INTO analysis(program, command, stLog, errorLog, date, exitCode, uuid, elapsedTime) VALUES('{}', \"{}\", '{}', '{}', '{}', {}, '{}', '{}')".format(
        program, command, stlog, erlog, data, exitcode, uuid, elapsed)
    with open(pathSql, "a") as fi:
        fi.write("{};\n".format(query))


def write_finished(path):
    '''
    Writes a ".finished file inside the analysis folder when a process has succesfully finished"
    '''

    try:
        open(path, 'a').close()
    except IOError:
        print >> sys.stderr, "WARNING: .finished file could not be created."


def already_run(path_to_analysis):
    if os.path.isfile(path_to_analysis + "/" + finish_file):
        print >> sys.stderr, "#############", path_to_analysis + "/" + finish_file
        return True
    else:
        if os.path.isdir(path_to_analysis):
            shutil.rmtree(path_to_analysis)
            print >> sys.stderr, "INFO: Analysis was unsuccessfully run before, analysis folder removed."

        return False


def runStrelka2Germline(bam, folder):
    '''
    Execute Strelka2 script and store the output and the log in a folder called strelkaGerm. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
    '''
    # Constant name of the Strelka folder. This folder will be created in the path passed as parameter
    strelkaFolder = "strelkaGerm"
    dirStrelka = "{}/{}".format(folder, strelkaFolder)
    # Useful later to store the info in the database
    erLog = dirStrelka + "/error.log"
    stLog = dirStrelka + "/output.log"
    uuid = folder.split("/")[-1]

    print >> sys.stderr, "INFO: Running Strelka2 germline in {}".format(folder)

    # Check if the analysis has been done before on the sample
    # if os.path.isdir(dirStrelka) :
    if already_run(dirStrelka):
        print >> sys.stderr, "WARNING: Strelka2 germline analysis has been done before. Not going to redo."
        return 0
    else:
        strt = time.time()
        com = '{}/runStrelka2.sh {} {}'.format(pathScripts, bam, dirStrelka)
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate()  # bash program output. Will be stored in log files

        if proc.returncode != 0:
            print >> sys.stderr, "WARNING: Strelka2 ran with errors. Check log"
            print >> sys.stderr, "\tCommand executed: {}".format(com)
            print >> sys.stderr, "\nERROR FOUND: ============================================\n{}\n============================================".format(
                sterr)

        try:
            # Store the outputs in logs
            with open(erLog, "a") as fi:
                fi.write(sterr)
            with open(stLog, "a") as fi:
                fi.write(stout)
        except IOError, e:
            print >> sys.stderr, "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(
                com, e)

        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "Strelka2 germline", com, stLog, erLog, proc.returncode, elapsedTime)

        if proc.returncode == 0:
            finish_flag = dirStrelka + "/" + finish_file
            write_finished(finish_flag)

        return proc.returncode


def runPlatypus(bam, folder):
    '''
    Execute Platypus script and store the output and the log in a folder called platypusGerm. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
    After that, store all the information about the analysis in the database
    '''
    platypusFolder = "platypusGerm"
    dirPlatypus = "{}/{}".format(folder, platypusFolder)
    uuid = folder.split("/")[-1]
    outLog = dirPlatypus + "/output.log"
    erLog = dirPlatypus + "/error.log"
    # com = "{}/runPlatypus.sh {} {}/platyGermline.vcf".format(pathScripts, bam,folder)
    com = "cd {};{}/runPlatypus.sh {} {}/platyGermline.vcf".format(folder, pathScripts, bam, folder)

    print >> sys.stderr, "INFO: Running Platypus germline in {}".format(folder)

    # Check if the analysis has been done before on the sample
    # if os.path.isdir(dirPlatypus) :
    if already_run(dirPlatypus):
        print >> sys.stderr, "WARNING: Platypus analysis has been done before. Not going to redo."
        return 0
    else:
        strt = time.time()
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate()
        if proc.returncode != 0:
            print >> sys.stderr, "WARNING: Platypus run with errors. Check log"
            print >> sys.stderr, "\tCommand executed: {}".format(com)
            print >> sys.stderr, "\nERROR FOUND: ============================================\n{}\n============================================".format(
                sterr)

        try:
            # Create the folder for Platypus and store them the output and the logs
            os.makedirs(dirPlatypus)
            with open(erLog, "a") as fi:
                fi.write(sterr)
            with open(outLog, "a") as fi:
                fi.write(stout)

            if proc.returncode == 0:
                os.rename(folder + "/platyGermline.vcf",
                          dirPlatypus + "/platyGermline.vcf")  # Move the output vcf to the corresponding folder
                # shutil.move("{}/log.txt".format(os.getcwd()), dirPlatypus + "/log.txt") #Move the log file created by Platypus to the corresponding folder
                shutil.move("{}/log.txt".format(folder),
                            dirPlatypus + "/log.txt")  # Move the log file created by Platypus to the corresponding folder

        except IOError, e:
            print >> sys.stderr, "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n{}".format(
                com, e)

        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "Platypus germline", com, outLog, erLog, proc.returncode, elapsedTime)

        if proc.returncode == 0:
            finish_flag = dirPlatypus + "/" + finish_file
            write_finished(finish_flag)

        return proc.returncode


def runCNVkit(folder):
    '''
     Execute CNVkit script and store the output and the log files in a passed folder as parameter. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
     After that, store all the information about the analysis in the database
    '''
    print >> sys.stderr, "INFO: Running CNVkit in {}".format(folder)
    erLog = folder + "/CNVkit/error.log"
    outLog = folder + "/CNVkit/output.log"
    uuid = folder.split("/")[-1]
    # Check if the analysis has been done before on the sample
    # if os.path.isdir(folder + "/CNVkit") :
    if already_run(folder + "/CNVkit"):
        print >> sys.stderr, "WARNING: CNVkit analysis has been done before. Not going to redo."
        return 0
    else:
        strt = time.time()
        com = "{}/runCNVkit.sh {}".format(pathScripts, folder)
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate()
        if proc.returncode != 0:
            print >> sys.stderr, "WARNING: CNVkit run with errors. Check log"
            print >> sys.stderr, "\tCommand executed: {}".format(com)
            print >> sys.stderr, "\nERROR FOUND: ============================================\n{}\n============================================".format(
                sterr)

        try:
            # Store logs. Logs will contain the output from two analyses: using a flat reference and using a pool reference
            with open(erLog, "a") as fi:
                fi.write(sterr)
            with open(outLog, "a") as fi:
                fi.write(stout)
        except IOError, e:
            print >> sys.stderr, "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(
                com, e)

        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "CNVkit", com, outLog, erLog, proc.returncode, elapsedTime)

        if proc.returncode == 0:
            finish_flag = folder + "/CNVkit/" + finish_file
            write_finished(finish_flag)

        return proc.returncode


def runEXCAVATOR2(bam, folder):
    '''
     Execute EXCAVATOR2 script and store the output and the log files in a folder passed as parameter. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
     After that, store all the information about the analysis in the database
    '''
    # get an alias for the bam that is necessary to run EXCAVATOR2 script
    alias = folder.split("/")[-2]
    uuid = folder.split("/")[-1]
    erLog = folder + "/EXCAVATOR2/error.log"
    outLog = folder + "/EXCAVATOR2/output.log"
    print >> sys.stderr, "INFO: Running EXCAVATOR2 in {}".format(folder)
    # Check if the analysis has been done before on the sample
    # if os.path.isdir(folder + "/EXCAVATOR2") :
    if already_run(folder + "/EXCAVATOR2"):
        print >> sys.stderr, "WARNING: EXCAVATOR2 analysis has been done before. Not going to redo."
        return 0
    else:
        strt = time.time()
        com = "{}/runEXCAVATOR2.sh {} {}".format(pathScripts, bam, alias)
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate()
        if proc.returncode != 0:
            print >> sys.stderr, "WARNING: EXCAVATOR2 run with errors. Check log"
            print >> sys.stderr, "\tCommand executed: {}".format(com)
            print >> sys.stderr, "\nERROR FOUND: ============================================\n{}\n============================================".format(
                sterr)

        try:
            # Store logs in EXCAVATOR2 folder
            with open(erLog, "a") as fi:
                fi.write(sterr)
            with open(outLog, "a") as fi:
                fi.write(stout)
        except IOError, e:
            print >> sys.stderr, "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(
                com, e)

        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "EXCAVATOR2", com, outLog, erLog, proc.returncode, elapsedTime)

        if proc.returncode == 0:
            finish_flag = folder + "/EXCAVATOR2/" + finish_file
            write_finished(finish_flag)

        return proc.returncode


def runStrelka2Somatic(bam, folder):
    '''
    Execute Strelka2 script for compare tumor vs normal, and store the output and the log files in a folder called UUIDtm_VS_UUIDnm. In case of excution error, it prints a warning message. If the folder exists, meaning the analysis has been done, it also prints a warning message
    After that, store all the information about the analysis in the database
    '''
    tc = getPair(bam, "Strelka2")

    if tc != None:
        #        if os.path.isdir(tc["folder"]) :
        if already_run(tc["folder"]):
            print >> sys.stderr, "WARNING:  Strelka2 somatic analysis was succesfully run before. Skipping"
        else:
            strt = time.time()
            erLog = tc["folder"] + "/error.log"
            stLog = tc["folder"] + "/output.log"
            uuid = folder.split("/")[-1]
            print >> sys.stderr, "INFO: Running Strelka2 comparing tumor vs normal in {}".format(folder)
            os.makedirs(tc["folder"])
            com = "{}/runStrelka2Somatic.sh {} {} {}".format(pathScripts, tc["normal"], tc["tumor"], tc["folder"])
            proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stout, sterr = proc.communicate()
            if proc.returncode != 0:
                print >> sys.stderr, "WARNING: Strelka2 somatic analysis exited with errors. Check log"
                print >> sys.stderr, "\tCommand executed: {}".format(com)
                print >> sys.stderr, "\nERROR FOUND: ============================================\n{}\n============================================".format(
                    sterr)

            try:
                with open(erLog, "a") as fi:
                    fi.write(sterr)
                with open(stLog, "a") as fi:
                    fi.write(stout)
            except IOError, e:
                print >> sys.stderr, "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(
                    com, e)

            end = time.time() - strt
            elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
            registerAnalysis(uuid, "Strelka2 somatic", com, stLog, erLog, proc.returncode, elapsedTime)

            if proc.returncode == 0:
                finish_flag = tc["folder"] + "/" + finish_file
                write_finished(finish_flag)

            return proc.returncode
    else:
        return 0


def runMSIsensor(bam, folder):
    tc = getPair(bam, "MSIsensor")
    exitCode = 0
    if tc != None:
        # if os.path.isdir(tc["folder"]) :
        if already_run(tc["folder"]):
            print >> sys.stderr, "WARNING: MSIsensor analysis has been done before. Not going to redo"
        else:
            strt = time.time()
            erLog = tc["folder"] + "/error.log"
            stLog = tc["folder"] + "/output.log"
            uuid = folder.split("/")[-1]
            print >> sys.stderr, "INFO: Running MSIsensor in {}".format(folder)
            com = "{}/runMSIsensor.sh {} {} {}".format(pathScripts, tc["tumor"], tc["normal"], tc["folder"])

            proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stout, sterr = proc.communicate()
            if proc.returncode != 0:
                print >> sys.stderr, "WARNING: MSIsensor ran with errors. Check log"
                print >> sys.stderr, "\tCommand executed: {}".format(com)
                print >> sys.stderr, "\nERROR FOUND: ============================================\n{}\n============================================".format(
                    sterr)

            try:
                with open(erLog, "a") as fi:
                    fi.write(sterr)
                with open(stLog, "a") as fi:
                    fi.write(stout)
            except IOError, e:
                print >> sys.stderr, "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(
                    com, e)

            end = time.time() - strt
            elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
            registerAnalysis(uuid, "MSIsensor", com, stLog, erLog, proc.returncode, elapsedTime)
            exitCode = proc.returncode

            if proc.returncode == 0:
                finish_flag = tc["folder"] + "/" + finish_file
                write_finished(finish_flag)

    return exitCode


def runMantaGermline(bam, folder):
    '''
    Execute Manta script for germline analysis. Store the output and the logs in a folder called mantaGerm. If there are execution errors, warning messages would be printedself.
    '''
    mantaFolder = "mantaGerm"
    dirManta = "{}/{}".format(folder, mantaFolder)
    erLog = dirManta + "/error.log"
    stLog = dirManta + "/output.log"
    uuid = folder.split("/")[-1]

    print >> sys.stderr, "INFO: Running Manta germline analysis in {}".format(folder)
    # if os.path.isdir(dirManta) :
    if already_run(dirManta):
        print >> sys.stderr, "WARNING: Manta germline has been done before. Skipping"
        return 0
    else:
        strt = time.time()
        com = "{}/runMantaGerminal.sh {} {}".format(pathScripts, bam, dirManta)
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate()  # bash program output. Will be stored in log files

        if proc.returncode != 0:
            print >> sys.stderr, "WARNING: Manta ran with errors. Check log"
            print >> sys.stderr, "\tCommand executed: {}".format(com)
            print >> sys.stderr, "\nERROR FOUND: ============================================\n{}\n============================================".format(
                sterr)

        try:
            # Store the outputs in logs
            with open(erLog, "a") as fi:
                fi.write(sterr)
            with open(stLog, "a") as fi:
                fi.write(stout)
        except IOError, e:
            print >> sys.stderr, "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(
                com, e)
        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "Manta germline", com, stLog, erLog, proc.returncode, elapsedTime)

        if proc.returncode == 0:
            finish_flag = dirManta + "/" + finish_file
            write_finished(finish_flag)

        return proc.returncode


def runMantaSomatic(bam, folder):
    tc = getPair(bam, "Manta")
    exitCode = 0
    if tc != None:
        # if os.path.isdir(tc["folder"]) :
        if already_run(tc["folder"]):
            print >> sys.stderr, "WARNING: Manta somatic was done before. Skipping"
        else:
            strt = time.time()
            erLog = tc["folder"] + "/error.log"
            stLog = tc["folder"] + "/output.log"
            uuid = folder.split("/")[-1]
            print >> sys.stderr, "INFO: Running Manta somatic analysis in {}".format(folder)
            com = "{}/runMantaSomatic.sh {} {} {}".format(pathScripts, tc["normal"], tc["tumor"], tc["folder"])
            proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stout, sterr = proc.communicate()  # bash program output. Will be stored in log files

            if proc.returncode != 0:
                print >> sys.stderr, "WARNING: Manta somatic ran with errors. Check log"
                print >> sys.stderr, "\tCommand executed: {}".format(com)
                print >> sys.stderr, "\nERROR FOUND: ============================================\n{}\n============================================".format(
                    sterr)

            try:
                # Store the outputs in logs
                with open(erLog, "a") as fi:
                    fi.write(sterr)
                with open(stLog, "a") as fi:
                    fi.write(stout)
            except IOError, e:
                print >> sys.stderr, "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(
                    com, e)

            end = time.time() - strt
            elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
            registerAnalysis(uuid, "Manta somatic", com, stLog, erLog, proc.returncode, elapsedTime)
            exitCode = proc.returncode

            if proc.returncode == 0:
                finish_flag = tc["folder"] + "/" + finish_file
                write_finished(finish_flag)

    return exitCode


def runFacets(bam, folder):
    tc = getPair(bam, "FACETS")
    exitCode = 0

    if tc != None:
        #        if os.path.isdir(tc["folder"]) :
        if already_run(tc["folder"]):
            print >> sys.stderr, "WARNING: FACETS was succesfully run before. Skipping"
        else:
            strt = time.time()
            erLog = tc["folder"] + "/error.log"
            stLog = tc["folder"] + "/output.log"
            uuid = folder.split("/")[-1]
            print >> sys.stderr, "INFO: Running FACETS analysis in {}".format(folder)
            com = "{}/runFacets.sh {} {} {}".format(pathScripts, tc["normal"], tc["tumor"], tc["folder"])
            proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stout, sterr = proc.communicate()  # bash program output. Will be stored in log files

            if proc.returncode != 0:
                print >> sys.stderr, "WARNING: FACETS ran with errors. Check log"
                print >> sys.stderr, "\tCommand executed: {}".format(com)
                print >> sys.stderr, "\nERROR FOUND: ============================================\n{}\n============================================".format(
                    sterr)

            try:
                # Store the outputs in logs
                with open(erLog, "a") as fi:
                    fi.write(sterr)
                with open(stLog, "a") as fi:
                    fi.write(stout)
            except IOError, e:
                print >> sys.stderr, "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(
                    com, e)

            end = time.time() - strt
            elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
            registerAnalysis(uuid, "FACETS", com, stLog, erLog, proc.returncode, elapsedTime)
            exitCode = proc.returncode

            if proc.returncode == 0:
                finish_flag = tc["folder"] + "/" + finish_file
                write_finished(finish_flag)

    return exitCode


def runAscatNgs(bam, folder, gender):
    tc = getPair(bam, "ASCAT")
    exitCode = 0
    if tc != None:
        # if os.path.isdir(tc["folder"]) :
        if already_run(tc["folder"]):
            print >> sys.stderr, "WARNING: AscatNGS was done before. Skipping"
        else:
            strt = time.time()
            erLog = tc["folder"] + "/error.log"
            stLog = tc["folder"] + "/output.log"

            uuid = folder.split("/")[-1]
            print >> sys.stderr, "INFO: Running AscatNGS in {}".format(folder)
            com = "{}/runAscat.sh {} {} {} {}".format(pathScripts, tc["normal"], tc["tumor"], tc["folder"], gender)
            print >> sys.stderr, com
            proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stout, sterr = proc.communicate()  # bash program output. Will be stored in log files

            if proc.returncode != 0:
                print >> sys.stderr, "WARNING: AscatNGS ran with errors. Check log"
                print >> sys.stderr, "\tCommand executed: {}".format(com)
                print >> sys.stderr, "\nERROR FOUND: ============================================\n{}\n============================================".format(
                    sterr)

            try:
                # Store the outputs in logs
                with open(erLog, "a") as fi:
                    fi.write(sterr)
                with open(stLog, "a") as fi:
                    fi.write(stout)
            except IOError, e:
                print >> sys.stderr, "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n\t{}".format(
                    com, e)

            end = time.time() - strt
            elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
            registerAnalysis(uuid, "AscatNGS", com, stLog, erLog, proc.returncode, elapsedTime)
            exitCode = proc.returncode

            if proc.returncode == 0:
                finish_flag = tc["folder"] + "/" + finish_file
                write_finished(finish_flag)

    return exitCode


def runBedtools(bam, folder):
    bedFolder = "genomeCoverage"
    dirBedtools = "{}/{}".format(folder, bedFolder)
    uuid = folder.split("/")[-1]
    outLog = dirBedtools + "/output.log"
    erLog = dirBedtools + "/error.log"
    print >> sys.stderr, "INFO: Running bedtools genomeCoverage in {}".format(folder)

    # if os.path.isdir(dirBedtools) :
    if already_run(dirBedtools):
        print >> sys.stderr, "WARNING: Bedtools genomeCov has been done before. Skipping"
        return 0
    else:
        strt = time.time()
        # com = "{}/runGenomeCov.sh {}".format(pathScripts, bam)
        com = "cd {};{}/runGenomeCov.sh {}".format(folder, pathScripts, bam)
        proc = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout, sterr = proc.communicate()
        if proc.returncode != 0:
            print >> sys.stderr, "WARNING: Bedtools genomeCoverage ran with errors. Check log"
            print >> sys.stderr, "\tCommand executed: {}".format(com)
            print >> sys.stderr, "\nERROR FOUND: ============================================\n{}\n============================================".format(
                sterr)

        try:
            # Create the folder for Bedtools and store them the output and the logs
            os.makedirs(dirBedtools)
            with open(erLog, "a") as fi:
                fi.write(sterr)
            with open(outLog, "a") as fi:
                fi.write(stout)

            if proc.returncode == 0:
                # shutil.move("{}/bamCoverage.tsv".format(os.getcwd()), dirBedtools + "/bamCoverage.tsv") #Move the output fileto the corresponding folder
                # shutil.move("{}/bamCoverage.tsv".format(folder), dirBedtools + "/bamCoverage.tsv") #Move the output file to the corresponding folder
                shutil.move("{}/bamCoverage.tsv.gz".format(folder),
                            dirBedtools + "/bamCoverage.tsv.gz")  # Move the output file gunzipped file

        except IOError, e:
            print >> sys.stderr, "ERROR : Something happened when storing the log files.\n\tCommand executed:\n\t{}\n\tDescription:\n{}".format(
                com, e)

        end = time.time() - strt
        elapsedTime = time.strftime("%H:%M:%S", time.gmtime(end))
        registerAnalysis(uuid, "Bedtools genomeCov", com, outLog, erLog, proc.returncode, elapsedTime)

        if proc.returncode == 0:
            finish_flag = dirBedtools + "/" + finish_file
            write_finished(finish_flag)

        return proc.returncode



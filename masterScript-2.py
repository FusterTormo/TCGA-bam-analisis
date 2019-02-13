import sqlite3
import sys
import os
import shutil
import re
import executeScripts as sc
import time

#Constants
pathDb = "/g/strcombio/fsupek_cancer2/TCGA_bam/info/info.db" #Absolute path where DB is stored
pathSql = "/g/strcombio/fsupek_cancer2/TCGA_bam/info/analyses_LUAD.sql"
cancerPath = {"HNSC" : "/g/strcombio/fsupek_cancer1/TCGA_bam",
        "LIHC" : "/g/strcombio/fsupek_cancer1/TCGA_bam",
        "LUAD" : "/g/strcombio/fsupek_cancer2/TCGA_bam",
        "LUSC" : "/g/strcombio/fsupek_cancer2/TCGA_bam",
        "OV" : "/g/strcombio/fsupek_cancer2/TCGA_bam",
        "STAD" : "/g/strcombio/fsupek_cancer2/TCGA_bam",
        "BLCA" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
        "BRCA" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
        "COAD" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
        "GBM" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
        "KICH" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
        "KIRC" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
        "KIRP" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
        "PAAD" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
        "PRAD" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
        "READ" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
        "THCA" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
        "UCEC" : "/g/strcombio/fsupek_cancer3/TCGA_bam"}

def getGender(id) :
    '''Searches the patient gender in the database. Return XX if the patient is a girl, XY if the patient is a boy'''
    q = "SELECT gender FROM patient WHERE submitter='{}'".format(id)
    db = sqlite3.connect(pathDb)
    with db :
        c = db.cursor()
        c.execute(q)
        a = c.fetchone()[0]
    if a == "female" :
        ret = "XX"
    elif a == "male" :
        ret = "XY"
    else :
        print "ERROR: Unable to find the gender in {}".format(id)
        sys.exit()

    return ret

def removebam(uuid, path) :
    print "INFO: Deleting the bam {}".format(path)
    #os.remove(path)
    query = "UPDATE sample SET deleted='Yes' WHERE uuid='{}'".format(uuid)
    with open(pathSql, "a") as fi :
        fi.write("{};\n".format(query))

def executeAnalysis(type, bam, folder, gender) :
    allOk = True #Know if all the scripts run successfully or not
    if type == "all" :
        if sc.runStrelka2Germline(bam, folder) != 0 :
            allOk = False
        if sc.runPlatypus(bam, folder) != 0 :
            allOk = False
        if sc.runCNVkit(folder) != 0 :
            allOk = False
        if sc.runEXCAVATOR2(bam, folder) != 0 :
            allOk = False
        if sc.runStrelka2Somatic(bam, folder) != 0 :
            allOk = False
        if sc.runMSIsensor(bam, folder) != 0 :
            allOk = False
        if sc.runMantaGermline(bam, folder) != 0 :
            allOk = False
        if sc.runMantaSomatic(bam, folder) != 0 :
            allOk = False
        if sc.runFacets(bam, folder) != 0 :
            allOk = False
        if sc.runAscatNgs(bam, folder, gender) != 0 :
            allOk = False
        if sc.runBedtools(bam, folder) != 0 :
            allOk = False
    elif type == "vcall" :
        if sc.runStrelka2Germline(bam, folder) != 0 :
            allOk = False
        if sc.runPlatypus(bam, folder) != 0 :
            allOk = False
        if sc.runStrelka2Somatic(bam, folder) != 0 :
            allOk = False
    elif type == "cnv" :
        if sc.runCNVkit(folder) != 0 :
            allOk = False
        if sc.runEXCAVATOR2(bam, folder) != 0 :
            allOk = False
        if sc.runMantaGermline(bam, folder) != 0 :
            allOk = False
        if sc.runMantaSomatic(bam, folder) != 0 :
            allOk = False
    elif type == "loh" :
        if sc.runFacets(bam, folder) != 0 :
            allOk = False
        if sc.runAscatNgs(bam, folder, gender) != 0 :
            allOk = False
    elif type == "msi" :
        if sc.runMSIsensor(bam, folder) != 0 :
            allOk = False
    elif type == "cov" :
        if sc.runBedtools(bam, folder) != 0 :
            allOk = False
    elif type == "strelka" :
        if sc.runStrelka2Germline(bam, folder) != 0 :
            allOk = False
    elif type == "strelkaS" :
        if sc.runStrelka2Somatic(bam, folder) != 0 :
            allOk = False
    elif type == "platypus" :
        if sc.runPlatypus(bam, folder) != 0 :
            allOk = False
    elif type == "cnvkit" :
        if sc.runCNVkit(folder) != 0 :
            allOk = False
    elif type == "excavator" :
        if sc.runEXCAVATOR2(bam, folder) != 0 :
            allOk = False
    elif type == "manta" :
        if sc.runMantaGermline(bam, folder) != 0 :
            allOk = False
    elif type == "mantaS" :
        if sc.runMantaSomatic(bam, folder) != 0 :
            allOk = False
    elif type == "facets" :
        if sc.runFacets(bam, folder) != 0 :
            allOk = False
    elif type == "ascat" :
        if sc.runAscatNgs(bam, folder, gender) != 0 :
            allOk = False

    return allOk

def readParams(args) :
    goodParams = True
    analysis = ""
    deleteBams = "no"
    #Check if is params 2 and 3 (type of analysis and delete bams) are valid option
    if args[2] not in ["all", "vcall", "cnv", "msi", "loh", "cov", "strelka", "strelkaS", "platypus", "cnvkit", "excavator", "manta", "mantaS", "facets", "ascat"] :
        print "ERROR: Bad second argument: {}".format(args[2])
        goodParams = False
    else :
        analysis = args[2]
    if args[3] not in ["y", "yes", "n", "no"] :
        print "ERROR: Bad third argument: {}".fomat(args[3])
        goodParams = False
    else :
        if args[3] == "y" or args[3] == "yes" :
            deleteBams = "yes"
    if not goodParams :
        usage()
    else :
        #Search in the database for the submitter id to get cancer and sample
        dbcon = sqlite3.connect(pathDb)
        with dbcon :
            c = dbcon.cursor()
            q = "SELECT cancer FROM patient WHERE submitter='{}'".format(args[1])
            try :
                c.execute(q)
                a = c.fetchone()
                if a == None :
                    raise IOError("ERROR: Submitter id {} not found in the database".format(args[1]))
                else :
                    cancer = a[0]
                    caseId = args[1]
                    absPath = "{}/{}/{}".format(cancerPath[cancer], cancer, caseId)
                    q = "SELECT uuid, bamName FROM sample WHERE submitter='{}'".format(caseId)
                    c.execute(q)
                    a = c.fetchall()
                    if a == None :
                        print "INFO: No samples found for the case. Exiting"
                        sys.exit(0)
            except sqlite3.OperationalError, e :
                print "ERROR: Found error while executing the query: {}\nDescription:\n{}".format(q, e)

        #Run analysis on each sample
        for s in a :
            fullPath = "{}/{}/{}".format(absPath,s[0],s[1])
            folder = sc.getFolder(fullPath)
            if deleteBams == "yes" :
                if executeAnalysis(args[2], fullPath, folder, getGender(args[1])) :
                    removebam(s[0], fullPath)
            else :
                executeAnalysis(args[2], fullPath, folder, getGender(args[1]))

def usage() :
    print "Expected parameters"
    print "\t[1] Submitter id for the case"
    print "\t[2] Analysis type: available values"
    print "\t\tall - All analyses"
    print "\t\tvcall - Only variant calling (Strelka2 germinal, Platypus, Strelka2 somatic)"
    print "\t\tcnv - Only copy number (CNVkit, EXCAVATOR2, Manta germinal, Manta somatic)"
    print "\t\tmsi - Only msi (MSIsensor)"
    print "\t\tloh - Only LOH (FACETS, AscatNGS)"
    print "\t\tcov - Only coverage (bedtools genomeCov)"
    print "\t\tstrelka - Only run Strelka2 germline"
    print "\t\tstrelkaS - Only run Strelka2 somatic"
    print "\t\tplatypus - Only run Platypus"
    print "\t\tcnvkit - Only run CNVkit"
    print "\t\texcavator - Only run EXCAVATOR2"
    print "\t\tmanta - Only run Manta germline"
    print "\t\tmantaS - Only run Manta somatic"
    print "\t\tfacets - Only run FACETS"
    print "\t\tascat - Only run AscatNGS"
    print "\t[3] If delete the bams after analysis. Possible values"
    print "\t\ty|yes - Delete the bams"
    print "\t\tn|no - Keep the bams"

def main() :
    ''' Runs the analysis specified by parameter in the submitter case passed as parameter. If user wants, bam files will be deleted
    Expected parameters
    [1] Submitter id for the case
    [2] Analysis type: available values
        all - All analyses
        vcall - Only variant calling (Strelka2 germinal, Platypus, Strelka2 somatic)
        cnv - Only copy number (CNVkit, EXCAVATOR2, Manta germinal, Manta somatic)
        msi - Only msi (MSIsensor)
        loh - Only LOH (FACETS, AscatNGS)
        cov - Only coverage (bedtools genomeCov)
        strelka - Only run Strelka2 germline
        strelkaS - Only run Strelka2 somatic
        platypus - Only run Platypus
        cnvkit - Only run CNVkit
        excavator - Only run EXCAVATOR2
        manta - Only run Manta germline
        mantaS - Only run Manta somatic
        facets - Only run FACETS
        ascat - Only run AscatNGS
    [3] If delete the bams after analysis. Possible values
        y|yes - Delete the bams
        n|no - Keep the bams
    '''
    start = time.time()
    if len(sys.argv) < 4 :
        usage()
    else :
        readParams(sys.argv)

main()

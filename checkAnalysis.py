import sqlite3
import masterScriptConstants as mc
import os
import time
import multiprocessing
import stat
import fnmatch
from shutil import rmtree, copyfile
from sys import stderr, exit

germlinePrograms = ["Strelka2 germline", "Platypus germline", "EXCAVATOR2", "CNVkit", "Manta germline", "Bedtools genomeCov"]
somaticPrograms = ["Strelka2 somatic", "AscatNGS", "FACETS", "Manta somatic", "MSIsensor"]

def getPairs(case) :
    '''Looks for how many tumor samples and normal samples has the case Id passed as parameter.
    Returns the combination of all tumors with all normals in a 2D list'''
    #Check how many tumors and normals are in the case
    tm = []
    cn = []
    comb = []
    connection = sqlite3.connect(mc.pathDb)
    with connection :
        query = "SELECT uuid FROM sample WHERE submitter='{}' AND tumor LIKE '%Tumor%'".format(case)
        c = connection.cursor()
        x = c.execute(query)
        for t in x.fetchall() :
            tm.append(t[0])
        query = "SELECT uuid FROM sample WHERE submitter='{}' AND tumor LIKE '%Normal%'".format(case)
        x = c.execute(query)
        for t in x.fetchall() :
            cn.append(t[0])
    #Check if all somatic analyses are done in each pair
    for t in tm :
        for n in cn :
            comb.append([t, n])

    return comb

def getAnalyses(program, pList) :
    '''Finds in pList all the pairs [program, exitCode] that has the same program passed as parameter'''
    subList = []
    for p in pList :
        if p[0] == program :
            subList.append(p)

    return subList

def createAnalysisDict(cancer, subs, gDict, sDict) :
    con = sqlite3.connect(mc.pathDb)

    with con :
        c = con.cursor()
        #Get all submitter id
        q = "SELECT s.submitter, uuid FROM sample s JOIN patient p ON s.submitter=p.submitter WHERE cancer='{}' ORDER BY s.submitter".format(cancer)
        a = c.execute(q)
        x = a.fetchall()
        for i in x :
            if not i[0] in subs.keys() : # Check if the submitter is already initialized
                subs[i[0]] = []
            subs[i[0]].append(i[1])

        #Get all analyses in the cancer for germline
        q = "SELECT uuid, program, exitCode FROM analysis WHERE program IN ('{}') AND uuid IN (SELECT uuid FROM sample s JOIN patient p ON p.submitter=s.submitter WHERE cancer='{}')".format("','".join(germlinePrograms), cancer)
        a = c.execute(q)
        x = a.fetchall()
        for i in x :
            if not i[0] in gDict.keys() : # Check if the uuid is already initialized
                gDict[i[0]] = []
            gDict[i[0]].append([i[1], i[2]])

        #Get all analyses in the cancer for somatic
        q = "SELECT command, program, exitCode FROM analysis WHERE program IN ('{}') AND uuid IN (SELECT uuid FROM sample s JOIN patient p ON p.submitter=s.submitter WHERE cancer='{}')".format("','".join(somaticPrograms), cancer)
        b = c.execute(q)
        x = b.fetchall()
        for i in x :
            #Transform command to UUIDtm_VS_UUIDnm
            aux = i[0].split(" ")[-1]
            if len(aux) < 3 :
                aux = i[0].split(" ")[-2] #Patch for Ascat command
            aux2 = aux.split("/")[-1]
            aux3 = aux2.split("_")
            if len(aux3) == 3 :
                uuid = aux2
            else :
                uuid = "_".join(aux3[:-1])
            #Check if the uuid is already initialized
            if not uuid in sDict.keys() :
                sDict[uuid] = []
            sDict[uuid].append([i[1], i[2]])

def checkGermline(cases, analyses) :
    #Case has list of uuids
    pending = []
    for c in cases :
        try :
            prs = analyses[c]
            for p in germlinePrograms :
                #Find all the analyses done using this program
                sublist = getAnalyses(p,prs)
                ispending = True
                for i in sublist :
                    if i[1] == 0 :
                        ispending = False
                        break

                if ispending :
                    pending.append([c, p])
        except KeyError :
            for er in germlinePrograms :
                pending.append([c, er])

    return pending

def checkSomatic(case, uuids, analyses) :
    pending = []
    comb = getPairs(case)
    for c in comb :
        aux1 = c[0].split("-")[0]
        aux2 = c[1].split("-")[0]
        root = "{}_VS_{}".format(aux1, aux2)
        try :
            prs = analyses[root]
            for s in somaticPrograms :
                ispending = True
                sublist = getAnalyses(s, prs)
                for i in sublist :
                    if i[1] == 0 :
                        ispending = False
                        break
                if ispending :
                    pending.append([c[0], c[1], s])
        except KeyError :
            for er in somaticPrograms :
                pending.append([c[0], c[1], er])

    return pending

def getDeletedBams(cases) :
    deleted = 0
    pending = 0
    if len(cases) > 0 :
        db = sqlite3.connect(mc.pathDb)
        with db :
            for c in cases :
                query = "SELECT deleted FROM sample WHERE submitter='{}'".format(c)
                cur = db.cursor()
                x = cur.execute(query)
                resps = x.fetchall()
                for i in resps :
                    if i[0] == "Yes" :
                        deleted += 1
                    elif i[0] == "No" :
                        pending += 1
                    else :
                        print "WARNING: Inconsistent value found in {}.\nQuery: ".format(i, query)

    return (deleted, pending)

def removeBams(cases) :
    db = sqlite3.connect(mc.pathDb)
    for c in cases :
        query = "SELECT cancer, s.submitter, uuid, bamName FROM sample s JOIN patient p ON s.submitter=p.submitter WHERE s.submitter='{}'".format(c)
        with db :
            cur = db.cursor()
            x = cur.execute(query)
            bams = x.fetchall()
        for b in bams :
            path = "{}/{}/{}/{}/{}".format(mc.cancerPath[b[0]], b[0], b[1], b[2], b[3])
            try :
                if os.path.isfile(path) :
                    print "INFO: Deleting the bam {}".format(path)
                    os.remove(path)
                    #Remove the bai, too
                    baiPath = path[0:-1] + 'i'
                    if os.path.isfile(baiPath) :
                        os.remove(baiPath)
            except OSError, e:
               print "ERROR: Unable to remove {}.\nDescription:\n\t{}".format(path, e)
            with db :
                cur = db.cursor()
                query = "UPDATE sample SET deleted='Yes' WHERE uuid='{}'".format(b[2])
                try :
                    x = cur.execute(query)
                except sqlite3.OperationalError, e :
                    print "ERROR: Error while executing the query {}.\nDescription:\n\t{}".format(e)

def checkSamples(cancer, askRemove = False) :
    done = []
    pending = []
    subs = {}
    gDict = {}
    sDict = {}
    counter = 0

    createAnalysisDict(cancer, subs, gDict, sDict)
    print "INFO: {} submitters found with bam files".format(len(subs))
    # print subs
    for s in subs :
        pendingGermline = checkGermline(subs[s], gDict)
        pendingSomatic = checkSomatic(s, subs[s], sDict)

        if len(pendingGermline) == 0 and len(pendingSomatic) == 0 :
            done.append(s)
        else :
            pending.append(s)

        if counter % 50 == 0:
            print "INFO: {} submitters checked from {}".format(counter, len(subs))

        counter += 1

    (removed, notRemoved) = getDeletedBams(done)

    if notRemoved > 0 and askRemove :
        opt = raw_input("Remove analysed bams? (y/n) ")
        if opt == "y" or opt == "Y" :
            removeBams(done)

def getErrorsInAnalysis(submitter, uuids, gDict, sDict) :
    comb = getPairs(submitter)
    errors = []
    # Get errors in germline
    for u in uuids :
        if u in gDict.keys() :
            for a in gDict[u] :
                if a[1] > 0 : #Error found check if it was solved or not
                    sublist = getAnalyses(a[0], gDict[u])
                    notSolved = True
                    for s in sublist :
                        if s[1] == 0 :
                            notSolved = False
                            break
                    if notSolved :
                        errors.append([submitter, a[0]])

    for u in comb :
        aux1 = u[0].split("-")[0]
        aux2 = u[1].split("-")[0]
        root = "{}_VS_{}".format(aux1, aux2)
        if root in sDict.keys() :
            for a in sDict[root] :
                if a[1] > 0 :
                    sublist = getAnalyses(a[0], sDict[root])
                    notSolved = True
                    for s in sublist :
                        if s[1] == 0 :
                            notSolved = False
                            break
                    if notSolved :
                        errors.append([submitter, a[0]])
    return errors

def getStats(cancer, askBash = True) :
    '''Return stats from the cancer passed as parameter. Some stats are:
    Number of samples pending to analyse
    Number of samples ready to delete
    Percentage of samples completely analysed
    Errors found
    Errors corrected'''
    done = []
    pending = []
    subs = {}
    gDict = {}
    sDict = {}
    counter = 0
    allPending = {}
    print "INFO: Getting all submitter Ids for {} cancer".format(cancer)
    dbcon = sqlite3.connect(mc.pathDb)
    with dbcon :
        c = dbcon.cursor()
        q = "SELECT submitter FROM patient WHERE cancer='{}'".format(cancer)
        x = c.execute(q)
        a = x.fetchall()

    print "INFO: {} submitters found".format(len(a))
    createAnalysisDict(cancer, subs, gDict, sDict)
    print "INFO: {} submitters found with bam files".format(len(subs))

    for s in subs :
        pendingGermline = checkGermline(subs[s], gDict)
        pendingSomatic = checkSomatic(s, subs[s], sDict)
        if len(pendingGermline) == 0 and len(pendingSomatic) == 0 :
            done.append(s)
        else :
            pending.append(s)
            allPending[s] = [pendingGermline, pendingSomatic]

        if counter % 50 == 0:
            print "INFO: {} submitters checked from {}".format(counter, len(subs))

        counter += 1

    unsolvedErrors = []
    aux1 = []
    print "INFO: Looking for unsolved errors"
    for i in pending :
        try :
            aux = getErrorsInAnalysis(i, subs[i], gDict, sDict)
            if aux != [] :
                unsolvedErrors.append(i)
        except :
            print "ERROR FOUND analysing {}".format(i)
            raise

    print "\n\t\t=========================================================================================="
    print "\t\t\t\t\t{} INFORMATION STATUS ({} cases)".format(cancer, len(a))
    print "\t\t=========================================================================================="
    print "\t\t- {} cases with pending analyses".format(len(pending))
    print "\t\t- {} cases with unsolved errors".format(len(unsolvedErrors))
    print "\t\t- {} cases completely analysed".format(len(done)+len(unsolvedErrors))
    print "\t\t\tCancer analysis status -> {} %".format(float(len(done)+len(unsolvedErrors))/float(len(a)) * 100)
    print "\t\t==========================================================================================\n"
    writePending(allPending, cancer, askBash)
    if askBash :
        print "\nINFO: List of pending analyses stored in ./pending.md"
        opt = raw_input("Create bash to execute all pending analyses? (y/n): ")
        if opt == 'y' or opt == 'Y':
            writeBash(allPending)
            print "\nINFO: Bash script stored as ./runPending.sh"

def writePending(samples, cancer, doGetBamsScript) :
    path = "{}/{}".format(mc.cancerPath[cancer], cancer)
    if doGetBamsScript :
        delBams = []
    program2Folder = {"Strelka2 germline" : "strelkaGerm", "Platypus germline" : "platypusGerm", "EXCAVATOR2" : "EXCAVATOR2", "CNVkit" : "CNVkit",
        "Manta germline" : "mantaGerm", "Bedtools genomeCov" : "genomeCoverage", "Strelka2 somatic" : "Strelka2", "AscatNGS" : "ASCAT",
        "FACETS" : "FACETS", "Manta somatic" : "Manta", "MSIsensor" : "MSIsensor"}
    with open("pending.md", "w") as fi :
        for k, v in samples.iteritems() :
            fi.write("## {}\n".format(k))
            if len(v[0]) > 0 :
                fi.write("### Germline\n")
                for g in v[0] :
                    fi.write("{}\t{}".format(g[0],g[1]))
                    dirAnalysis = "{}/{}/{}/{}".format(path,k, g[0], program2Folder[g[1]])
                    dirSample = "{}/{}/{}".format(path,k,g[0])
                    if os.path.isdir(dirAnalysis) :
                        if isError(g[1], g[0]) :
                            fi.write("\n{} **ERROR IN ANALYSIS**\n".format(dirAnalysis))
                        else :
                            fi.write("\n{} **FOLDER EXISTS**\n".format(dirAnalysis))
                    else :
                        fi.write("\n")
                    if bamDeleted(dirSample) :
                        fi.write("\n{}\t**BAM DELETED**\n".format(dirSample))
                        if doGetBamsScript :
                            if k not in delBams :
                                delBams.append(k)
            if len(v[1]) > 0 :
                fi.write("\n### Somatic\n")
                for s in v[1] :
                    aux1 = s[0].split("-")[0]
                    aux2 = s[1].split("-")[0]
                    somaticFolder = "{}_VS_{}_{}".format(aux1, aux2, program2Folder[s[2]])
                    dirAnalysis = "{}/{}/{}".format(path,k,somaticFolder)
                    dirSample1 = "{}/{}/{}".format(path,k,s[0])
                    dirSample2 = "{}/{}/{}".format(path,k,s[1])
                    fi.write("{}\t{}\t{}".format(s[0],s[1],s[2]))
                    if os.path.isdir(dirAnalysis) :
                        if isError(s[2], s[0], s[1]) :
                            fi.write("\n{} **ERROR IN ANALYSIS**\n".format(dirAnalysis))
                        else :
                            fi.write("\n{} **FOLDER EXISTS**\n".format(dirAnalysis))
                    else :
                        fi.write("\n")
                    if bamDeleted(dirSample1) :
                        fi.write("\n{}\t**BAM DELETED**\n".format(dirSample1))
                        if doGetBamsScript :
                            if k not in delBams :
                                delBams.append(k)
                    if bamDeleted(dirSample2) :
                        fi.write("\n{}\t**BAM DELETED**\n".format(dirSample2))
                        if doGetBamsScript :
                            if k not in delBams :
                                delBams.append(k)
            fi.write("\n")

    if doGetBamsScript and len(delBams) > 0:
        with open("{}/redownloadedbams.sql".format(path),"w") as fi :
            for i in delBams :
                fi.write("UPDATE sample SET deleted='No' WHERE submitter='{}';\n".format(str(i)))

        # Create a new getBams.sh to download the bams that were accidentally deleted before do all the analyses
        with open("{}/getBams.sh".format(path), "w") as fi :
            fi.write("#!/bin/bash\n\n")
            fi.write("cd {}\n".format(path))
            fi.write("ar=( {} )\n\n".format(" ".join(delBams)))
            fi.write("sta=`date`\n")
            fi.write("token='/mnt/data/token.txt'\n")
            fi.write("gdc='/mnt/data/gdc-client download'\n")
            fi.write("for f in \"${ar[@]}\"; do\n")
            fi.write("\trm $f/*/logs/*parcel\n")
            fi.write("\techo \"Getting $f. Started at `date`\"\n")
            fi.write("\tcd $f\n")
            fi.write("\t$gdc -t $token -m $f.txt -d . -n 40\n")
            fi.write("\techo -e \"Finished at `date`\\n\"\n")
            fi.write("\tcd ..\n")
            fi.write("done\n")
            fi.write("echo -e \"getBams.sh started on $sta\n\ngetBams.sh ended on `date`\"\n")
            fi.write("echo -e \"Updating database\"\n")
            fi.write("tcgadb \".read {}/redownloadedbams.sql\"\n".format(path))

        print "WARNING: Found deleted bams on cases where not all analyses where performed. Created bash script in {} folder to download these samples".format(path)

def writeBash(samples) :
    #TODO mover los bash scripts que queden pendientes
    #print samples # Imprime una lista. Cada elemento de la lista es una lista compuesta por el uuid [uuid2 si el analisis es somatico] y el nombre del programa que queda pendiente
    #Consulta a la base de datos para recoger el submitter
    #select submitter from sample where uuid='%UUID%';

    #TODO crear una funcion para borrar las carpetas de todos los analisis que no han funcionado
    #Dictionary to convert the name stored in the database for the program to the name used in masterSciptLib
    convert2master = {"Strelka2 germline" : "strelka", "Platypus germline" : "platypus", "EXCAVATOR2" : "excavator", "CNVkit" : "cnvkit",
     "Manta germline" : "manta", "Bedtools genomeCov" : "cov", "Strelka2 somatic" : "strelkaS", "AscatNGS" : "ascat", "FACETS" : "facets",
     "Manta somatic" : "mantaS", "MSIsensor" : "msi"}
    filename = "runPending.sh"
    pathMasterScript = "/home/ffuster/Scripts/masterScriptLib.py"
    with open(filename, "w") as fi :
        fi.write("#!/bin/bash\n\n")
        for k, v in samples.iteritems() :
            if len(v[0]) > 0 :
                for g in v[0] :
                    fi.write("python {} {} {} no\n".format(pathMasterScript, k, convert2master[g[1]]))
            if len(v[1]) > 0 :
                for s in v[1] :
                    fi.write("python {} {} {} no\n".format(pathMasterScript, k, convert2master[s[2]]))

    os.chmod(filename, stat.S_IRWXU)

def bamDeleted(folder) :
    noBam = True
    for root, dirs, files in os.walk(folder) :
        for name in files:
            if fnmatch.fnmatch(name, '*.bam'):
                noBam = False
                break
        break

    return noBam

def isError(program, bam1, bam2=None) :
    error = True
    dbcon = sqlite3.connect(mc.pathDb)
    with dbcon :
        c = dbcon.cursor()
        if bam2 == None :
            q = "SELECT exitCode FROM analysis WHERE program='{}' AND uuid='{}'".format(program, bam1)
        else :
            aux1 = bam1.split("-")[0]
            aux2 = bam2.split("-")[0]
            somaticFolder = "{}_VS_{}".format(aux1, aux2)
            q = "SELECT exitCode FROM analysis WHERE program='{}' AND command LIKE '%{}%'".format(program, somaticFolder)
        x = c.execute(q)
        codes = x.fetchall()

    if len(codes) > 0 :
        for c in codes :
            if c[0] == 0 :
                error = False
                break

    return error
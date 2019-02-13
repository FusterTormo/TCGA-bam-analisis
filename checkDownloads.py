import os
import sqlite3
import masterScriptConstants as mc

def getCancers() :
    notFolder = ["info", "batches"]
    current = []
    cancers = []
    for i in range(1,4) :
        folder = "/g/strcombio/fsupek_cancer{}/TCGA_bam".format(i)
        for dirname, dirnames, filenames in os.walk(folder):
            # Get the cancers. There are temporary folders, where the cancer is not completely downloaded
            for subdirname in dirnames:
                if subdirname not in notFolder and subdirname not in cancers and not subdirname.startswith("TCGA-"):
                    cancers.append(subdirname)
                elif subdirname.startswith("TCGA-"): #Store the currently downloading cancers
                    current.append(subdirname)
            break
    #Remove currently downloading cancers from the list
    if len(current) > 0 :
        for i in current :
            pendingCancer = i.split("-")[1]
            ndx = cancers.index(pendingCancer)
            del cancers[ndx]

    cancers.sort()
    return cancers

def cancersInDb() :
    con = sqlite3.connect(mc.pathDb)
    cancers = []
    with con :
        q = "SELECT DISTINCT cancer FROM patient ORDER BY cancer"
        c = con.cursor()
        x = c.execute(q)
        a = x.fetchall()
    for c in a :
        cancers.append(str(c[0]))

    return cancers


def main () :
    """Check if there are pending cancer information to store in the database. Checks the cancer folders and the database and compares the number of fully downloaded cancers.
    If the database is not up to date, prints which cancers are pending to store in the database and some help about how to update the database"""
    cancerStored = getCancers()
    cancerDB = cancersInDb()
    pending = []
    for c in cancerStored :
        try :
            bulk = cancerDB.index(c)
        except ValueError :
            pending.append(c)

    if len(pending) > 0 :
        print "INFO: Database is not updated, there are {} pending cancers to store in the database:\n\t-> {}".format(len(pending), ", ".join(pending))
        print "Update the data using python listBams-2.py to get the sample data. And downloading clinical data from the cancer, and converting to patient data using python json2DB.py (modify this script changing the clinical data filename, and cancer type)"
    else :
        print "INFO: Database is updated. No changes needed."

if __name__ == "__main__" :
    main()

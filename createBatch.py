import sqlite3
import sys
import os
import masterScriptConstants as msc
import time

date_string = time.strftime("%Y,%m,%d")
date = date_string.replace(",", "")

#Constants
batchFolder = "/g/strcombio/fsupek_cancer2/TCGA_bam/batches"
scriptsFolder = "/g/strcombio/fsupek_cancer2/sc_repo"

def getHeader(id, cpus, ram, log, timeSpent) :
    str = "#!/usr/bin/bash\n\
#\n\
# Specify name of job allocation\n\
#SBATCH --job-name={}{} \n\
#\n\
# Instruct Slurm to connect the batch script's standard output directly\n\
# to the file name specified in the \"filename pattern\". By default both\n\
# standard output and standard error are directed to the same file\n\
#SBATCH --output={}{}.log\n\
#\n\
# Specify number of tasks, in general --ntasks should always be equal to 1 (unless you use MPI)\n\
#SBATCH --ntasks=1\n\
#\n\
# Specify CPUs per task, if your application requires n threads, then set --cpus-per-tasks=n (unless MPI is being used)\n\
#SBATCH --cpus-per-task={}\n\
#\n\
# Specify the minimum memory required per allocated CPU\n\
#SBATCH --mem={}\n\
# Specify the maximum time the job can spend\n\
# #SBATCH --time={}\n\
#\n\
# Force the jobs to be run in old node (temporal solution for concurrent IO problems from the 2 servers to synology)\n\
# #SBATCH -w fsupeksvr\n\
# Run \n".format(log, id, log, id, cpus, ram, timeSpent)
    return str

def run(cancer) :
    #Go to database and extract all submitters for cancers
    db = sqlite3.connect(msc.pathDb)
    count = 0
    hundreds = 100
    count_j = 0

    list_options = ', '.join(msc.job_specs.keys())

    opt = raw_input("For which analyses you want to create batch scripts? (" + list_options + "): ")
    opt = opt.lower()

    if opt not in msc.job_specs.keys() :
        raise KeyError("Invalid option for batch scripts")
    else :
        jobSpecs = msc.job_specs[opt]

    batch_folder = "{}_{}_{}".format(batchFolder, cancer, date)

    if not os.path.exists(batch_folder) :
         os.makedirs(batch_folder)
         print >> sys.stderr, "INFO: batchFolder created: ", batch_folder
    else :
        print >> sys.stderr, "INFO: batchFolder already exists: ", batch_folder

    batch_folder_opt = "{}/{}".format(batch_folder, opt)

    if not os.path.exists(batch_folder_opt) :
         os.makedirs(batch_folder_opt)
         print >> sys.stderr, "INFO: batchFolder created: ", batch_folder_opt
    else:
         print >> sys.stderr, "ERROR: batchFolder already exists ", batch_folder_opt
         sys.exit(0)

    partial = "{}/run{}to{}_{}_{}.sh".format(batch_folder_opt, count, hundreds, opt, cancer)
    print "INFO: Getting submitter IDs for {}".format(cancer)
    with db :
        c = db.cursor()
        q = "SELECT submitter FROM patient WHERE cancer='{}'".format(cancer)
        a = c.execute(q)
        submitters = a.fetchall()

    for i in submitters :
        bash = "{}/runAll_{}_{}_samples.sh".format(batch_folder_opt, opt, cancer)
        count += 1

        if count % 100 == 0 :
            hundreds += 100
            partial = "{}/run{}to{}_{}_{}.sh".format(batch_folder_opt, count, hundreds, opt, cancer)

        if not os.path.isfile(bash) :
            with open(bash, "w") as fi :
                fi.write("#! /usr/bin/bash\n\n")

        if not os.path.isfile(partial) :
            with open(partial, "w") as fi :
                fi.write("#! /usr/bin/bash\n\n")

        for k in jobSpecs.keys() :
            count_j += 1
            if count_j % 70 == 0:
                # print "Count {}".format(count)
                with open(partial, "a") as fi:
                    fi.write("sleep 3600\n")
                with open(bash, "a") as fi:
                    fi.write("sleep 3600\n")

            head = getHeader(i[0], jobSpecs[k][0], jobSpecs[k][1], jobSpecs[k][2], jobSpecs[k][3])
            batchFile = "{}/batch_{}_{}.sh".format(batch_folder_opt,i[0], k)

            with open(batchFile, "w") as fi :
                fi.write(head)
                fi.write("srun python {}/masterScript-2.py {} {} no\n".format(scriptsFolder, i[0], k))

            with open(bash, "a") as fi :
                fi.write("sbatch {}\n".format(batchFile))

            with open(partial, "a") as fi :
                fi.write("sbatch {}\n".format(batchFile))

    print "INFO: Batch files and bash to send the jobs created in {}".format(batch_folder_opt)

def main() :
    print "UNDER CONSTRUCTION"
    sys.exit()
    if sys.argv != 2 :
        opc, b = GUI()
        run(opc, b)
    else :
        if sys.argv[1] in list(msc.cancerPath.keys()) :
            if sys.argv[2] == "y" :
                b = True
            elif sys.argv[2] == "n" :
                b = False
            else :
                raise IOError("Not available option for batch Script")

            run(sys.argv[1], b)
        else :
             opc, b = GUI()
             run(opc, b)

if __name__ == "__main__" :
    main()


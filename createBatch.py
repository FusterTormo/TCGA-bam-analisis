import sqlite3
import sys
import os
import masterScriptConstants as msc

#Constants
batchFolder = "/g/strcombio/fsupek_cancer2/TCGA_bam/batches"
# batchFolder = "/g/strcombio/fsupek_cancer2/TCGA_bam/batches_KIRP_20190201"
# batchFolder = "/g/strcombio/fsupek_cancer2/TCGA_bam/batches_READ_20190215"
# batchFolder = "/g/strcombio/fsupek_cancer2/TCGA_bam/batches_THCA_20190219"
# batchFolder = "/g/strcombio/fsupek_cancer2/TCGA_bam/batches_BRCA_20190220"

scriptsFolder = "/g/strcombio/fsupek_cancer2/sc_repo"
jobSpecs = { "strelka" : ["8", "2G", "strelka2G_", "02:00:00"],
             "strelkaS" : ["8", "2G", "strelka2S_", "02:00:00"],
             "platypus" : ["1", "1G", "platypus_", "50:00"],
             # "cnvkit" : ["8", "10G", "cnvkit_" , "30:00"], # dropped from the tools to run 2019/02/01
             # "excavator" : ["20", "1G", "excavator2_", "01:30:00"], # dropped from the tools to run 2019/02/01
             # "manta" : ["6", "2G", "mantaG_", "01:30:00"], # dropped from the tools to run 2019/02/01
             "mantaS" : ["6", "2G", "mantaS_", "03:00:00"],
             "facets" : ["1", "1G", "facets_", "05:00:00"],
             # "ascat" : ["2", "16G", "ascat_", "14:00:00"],
	         # "ascat" : ["2", "22G", "ascat_", "14:00:00"], # dropped from the tools to run 2019/02/01
             "msi" : ["10", "1G", "msisensor_", "01:00:00"],
             "cov" : ["1", "10G", "bedtoolsCov_", "02:30:00"]}

# modified to increase time of execution due to synology problem (cancer3)
#jobSpecs = { "strelka" : ["8", "2G", "strelka2G_", "04:00:00"],
#        "strelkaS" : ["8", "2G", "strelka2S_", "04:00:00"],
#        "platypus" : ["1", "1G", "platypus_", "04:00:00"],
#        "cnvkit" : ["8", "10G", "cnvkit_" , "03:00:00"],
#        "excavator" : ["20", "1G", "excavator2_", "06:00:00"],
#        "manta" : ["6", "2G", "mantaG_", "06:00:00"],
#        "mantaS" : ["6", "2G", "mantaS_", "12:00:00"],
#        "facets" : ["1", "1G", "facets_", "10:00:00"],
#        "ascat" : ["2", "16G", "ascat_", "40:00:00"],
#        "msi" : ["10", "1G", "msisensor_", "04:00:00"],
#        "cov" : ["1", "10G", "bedtoolsCov_", "10:30:00"]}

## OJO!!!!!
## Time limit suppressed 21/12/2018 to avoid jobs to be cancelled due to time limit 
## Time limit used again from 15/02/2019, raise priority

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
#SBATCH --time={}\n\
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
    partial = "{}/run{}to{}_{}.sh".format(batchFolder, count, hundreds, cancer)
    print "INFO: Getting submitter IDs for {}".format(cancer)
    with db :
        c = db.cursor()
        q = "SELECT submitter FROM patient WHERE cancer='{}'".format(cancer)
        a = c.execute(q)
        submitters = a.fetchall()
    for i in submitters :
        bash = "{}/runAll{}samples.sh".format(batchFolder, cancer)
        count += 1
        if count % 100 == 0 :
            hundreds += 100
            partial = "{}/run{}to{}_{}.sh".format(batchFolder, count, hundreds, cancer)

        if not os.path.isfile(bash) :
            with open(bash, "w") as fi :
                fi.write("#! /usr/bin/bash\n\n")

        if not os.path.isfile(partial) :
            with open(partial, "w") as fi :
                fi.write("#! /usr/bin/bash\n\n")

        for k in jobSpecs.keys() :
            head = getHeader(i[0], jobSpecs[k][0], jobSpecs[k][1], jobSpecs[k][2], jobSpecs[k][3])
            batchFile = "{}/batch_{}_{}.sh".format(batchFolder,i[0], k)
            with open(batchFile, "w") as fi :
                fi.write(head)
                fi.write("srun python {}/masterScript-2.py {} {} no\n".format(scriptsFolder, i[0], k))

            with open(bash, "a") as fi :
                fi.write("sbatch {}\n".format(batchFile))

            with open(partial, "a") as fi :
                fi.write("sbatch {}\n".format(batchFile))

    print "INFO: Batch files and bash to send the jobs created in {}".format(batchFolder)

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


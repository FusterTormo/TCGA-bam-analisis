library("facets")

#Get command line arguments. 
sysarg <- commandArgs(trailingOnly = TRUE)

# running the stomach example in the vignette 
datafile = sysarg[1]
cat ("INFO: Executing FACETS in ", datafile[1], "\n")

# read the data
rcmat = readSnpMatrix(datafile)
# fit segmentation tree
xx = preProcSample(rcmat)
# estimate allele specific copy numbers. The small cval is, the more sensitive for small changes
oo=procSample(xx,cval=150)
# EM fit version 1
fit=emcncf(oo)
plotSample(oo, emfit = fit)

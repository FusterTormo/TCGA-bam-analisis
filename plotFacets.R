library("facets")

#Get command line arguments. 
sysarg <- commandArgs(trailingOnly = TRUE)

#First parameter in R script is the folder where the FACETS has been executed
folder = sysarg[1][1]

#cat ("INFO: Executing FACETS in ", folder, "\n")
setwd(folder)

#Maintain the randomization
set.seed(1234)

cat ("INFO: Executing FACETS in facets_comp.csv\n")
# read the data
rcmat = readSnpMatrix("facets_comp.csv")

# fit segmentation tree
xx = preProcSample(rcmat)
# estimate allele specific copy numbers. The small cval is, the more sensitive for small changes
oo = procSample(xx,cval=150)
# EM fit version 1
fit = emcncf(oo)
cat ("INFO: Storing info\n")
write.table(fit$cncf, file="facets_comp_cncf.tsv", sep="\t", row.names = FALSE)
basic <- data.frame(fit$loglik, fit$purity, fit$ploidy, fit$dipLogR)
colnames(basic) <- c("Log_likelihood", "Purity", "Ploidy", "Estimated_logR_diploid_segments")
write.table(basic, file="facets_comp_basic.tsv", sep="\t", row.names = FALSE)
png("facets_comp.png", width = 900, height = 900, units = "px", pointsize = 18)
plotSample(oo, emfit = fit)
dev.off()
cat ("INFO: Data stored succesfully:\n\tfacets_comp_cncf -> Contains the columns of segmentation output\n\tfacets_comp_basic.tsv -> Contains information about purity, ploidy ...\n")
cat ("\tfacets_comp.png -> Contains the plot generated using FACETS plotSample command\n")

cat ("INFO: Executing FACETS in facets_comp_w_Windows.csv\n")
rcWin = readSnpMatrix("facets_comp_w_Windows.csv")
# fit segmentation tree
xxWin = preProcSample(rcWin)
# estimate allele specific copy numbers. The small cval is, the more sensitive for small changes
ooWin = procSample(xxWin,cval=150)
# EM fit version 1
fitWin = emcncf(ooWin)
cat ("INFO: Storing info\n")
write.table(fitWin$cncf, file="facets_comp_w_Windows_cncf.tsv", sep="\t", row.names = FALSE)
basicWin <- data.frame(fitWin$loglik, fitWin$purity, fitWin$ploidy, fitWin$dipLogR)
colnames(basicWin) <- c("Log_likelihood", "Purity", "Ploidy", "Estimated_logR_diploid_segments")
write.table(basicWin, file="facets_comp_w_Windows_basic.tsv", sep="\t", row.names = FALSE)
png("facets_comp_w_Windows.png", width = 900, height = 900, units = "px", pointsize = 18)
plotSample(oo, emfit = fit)
dev.off()
cat ("INFO: Data stored succesfully:\n\tfacets_comp_cncf_w_Windows -> Contains the columns of segmentation output\n\tfacets_comp_basic.tsv -> Contains information about purity, ploidy ...\n")
cat ("\tfacets_comp.png -> Contains the plot generated using FACETS plotSample command\n")

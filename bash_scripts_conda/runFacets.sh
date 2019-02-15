#!/usr/bin/env bash

source ~/anaconda2/etc/profile.d/conda.sh

## snpPileup=/home/dortiz/bio/software/facets/inst/extcode/snp-pileup
## vcf=~/genome_references/1000GENOMES-phase_3.vcf.gz #Reference vcf file with the SNPs to look for SNPs.
vcf=/g/strcombio/fsupek_home/ffuster/genome_references/1000GENOMES-phase_3.vcf.gz

facets_sc=/g/strcombio/fsupek_cancer2/sc_repo/run_facets.R

normal=$1 #Absolute path for normal bam
tumor=$2 #Abolute path for tumor bam
#The program will create 2 different outputs. One only for the regions in the vcf, and the other inserting a blank record every 100 positions if there is no SNP before
output=$3/facets_comp.csv 
output2=$3/facets_comp_w_Windows.csv

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

if (( $# == 3 ))
then
	SECONDS=0
	sta=`date`
	
	# Activate conda environment
 	conda activate facets

	#Check if the output dir exists. Create in case it does not
	if [ ! -d $3 ]
	then
		mkdir $3
	fi

	#FACETS expects to have 2 bams: First the control and second the tumor
	# $snpPileup -P100 $vcf $output2 $normal $tumor
        snp-pileup -P100 $vcf $output2 $normal $tumor
	printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
	
	# $snpPileup $vcf $output $normal $tumor
	snp-pileup $vcf $output $normal $tumor
	
	# Run facets 
	Rscript $facets_sc  -c ${output} -o $3
        Rscript $facets_sc  -c ${output2} -o $3
	
	if (( $? == 0 ))
	then
		echo -e "${GREEN}snp-pileup ran successfully.${NC}\n"
	else 
		echo -e >&2 "\n${RED}Execution aborted. Check below possible errors${NC}\n"
		exit 1
	fi
	end=`date`
	echo -e "snp-pileup started at $sta\nEnded at $end"
	printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
	conda deactivate
else
	echo -e >&2 "\nUSAGE: runFacets.sh normal.bam tumor.bam output_directory\n" #Print the output using stderr
	exit 1
fi

#!/usr/bin/env bash

source ~/anaconda2/etc/profile.d/conda.sh

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

if (( $# == 1 ))
then
	conda activate cnvkit
	#Check if the references exists. Create the references in case
	## pool=~/genome_references/cnvkit/germlinePool.reference.cnn
	pool=/g/strcombio/fsupek_home/ffuster/genome_references/cnvkit/germlinePool.reference.cnn
	## flat=~/genome_references/cnvkit/germlineFlat.reference.cnn
	flat=/g/strcombio/fsupek_home/ffuster/genome_references/cnvkit/germlineFlat.reference.cnn

	if [ ! -f $pool ]
	then
		echo -e "\n${RED}Pool reference not found.${NC}\nCompiling a new one. This will take some time ...\n"
		$HOME/git/bam-anal-isis/repository/createCNVkitPoolReference.sh
	fi
	if [ ! -f $flat ]
	then
		echo -e "\n${RED}Flat reference not found.${NC}\n Compiling a new one.\n"
		$HOME/git/bam-anal-isis/repository/createCNVkitFlatReference.sh
	fi

	sta=`date`
	SECONDS=0
	cd $1

	#Output will stored in CNVkit folder; in CNVkit/poolRef output running CNVkit with a pool reference; in CNVkit/flatRef output with a flat reference
	mkdir CNVkit
	mkdir CNVkit/poolRef
	mkdir CNVkit/flatRef
	cnvkit.py batch	*.bam -r $pool -d ./CNVkit/poolRef -p 8 
	cnvkit.py batch *.bam -r $flat -d ./CNVkit/flatRef -p 8
	if (( $? == 0 )); then
		echo -e "${GREEN}CNVkit ran successfully.${NC}\n"
	else 
		echo -e >&2 "\n${RED}Execution aborted. Check below possible errors${NC}\n"
		exit 1
	fi
	end=`date`
	echo -e "CNVkit started at $sta\nEnded at $end"
	printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
	conda deactivate
else
	echo -e >&2 "\n\nUSAGE: runCNVkit.sh input_directory\n"
	echo -e >&2 "input_directory -> folder where the bam files to analyze are stored\n\n"
	exit 1
fi


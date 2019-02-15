#!/usr/bin/env bash

source ~/anaconda2/etc/profile.d/conda.sh

#Run Platypus with default parameters. Needs input bam as parameter 1, and output vcf as parameter 2
## reference=~/genome_references/GRCh38.d1.vd1.fa
reference=/g/strcombio/fsupek_home/ffuster/genome_references/GRCh38.d1.vd1.fa

#Colores para colorear el texto que se imprime en el bash
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

#Check if the number of parameters is the expected and run Platypus if it is the case
if (( $# == 2 )); then
	conda activate platypus
	sta=`date`
	SECONDS=0
	
	platypus callVariants --bamFiles=$1 --refFile=$reference --output=$2 --verbosity=1
	#Check if Platypus ended successfully
	if (( $? == 0 )); then
		echo -e "${GREEN}Platypus ran successfully.${NC}"
		
		end=`date`
		echo -e "Platypus started at $sta\nEnded at $end"
		printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
		conda deactivate
	else
		echo -e >&2 "\n${RED}Execution aborted. Check below possible errors${NC}\n"
		conda deactivate
		exit 1
	fi	
else 
	echo -e >&2 "\n\nUSAGE: runPlatypus.sh input.bam output.vcf\n\n"
	exit 1
fi

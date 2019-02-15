#!/usr/bin/env bash

source ~/anaconda2/etc/profile.d/conda.sh

#Run Strelka2 with default parameters for tumor vs control analysis. Needs input normal bam as parameter 1, input tumor bam as parameter2, and output directory as parameter 3
## reference=~/genome_references/GRCh38.d1.vd1.fa
reference=/g/strcombio/fsupek_home/ffuster/genome_references/GRCh38.d1.vd1.fa

strelka=configureStrelkaSomaticWorkflow.py
#Color constants to print in different colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

#Check if the number of parameters is the expected and run Strelka if it is the case
if (( $# == 3 )); then
	conda activate strelka
	sta=`date`
	SECONDS=0

	$strelka --normalBam $1 --tumorBam $2 --referenceFasta $reference --exome --runDir $3
	if (( $? == 0 )); then
		echo -e "\n\n${GREEN}Strelka-2 configured successfully.${NC} Running the analysis\n\n"
		$3/runWorkflow.py -m local -j 8 --quiet
		if (( $? == 0 )); then
			echo -e "${GREEN}Strelka-2 ran successfully.${NC} Results stored in $3"
			
			end=`date`
			echo -e "Strelka-2 started at $sta\nEnded at $end"
			printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
			conda deactivate
		fi
	else
		echo -e >&2 "\n${RED}Execution aborted. Check below possible errors${NC}\n"
		conda deactivate
		exit 1
	fi
else 
	echo -e >&2 "\nUSAGE: runStrelka2Somatic.sh normal.bam tumor.bam output_directory\n"
	exit 1
fi


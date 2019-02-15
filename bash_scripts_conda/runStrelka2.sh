#!/usr/bin/env bash

source ~/anaconda2/etc/profile.d/conda.sh

#Run Strelka2 with default parameters. Needs input bam as parameter 1, and output directory as parameter 2
## reference=~/genome_references/GRCh38.d1.vd1.fa
reference=/g/strcombio/fsupek_home/ffuster/genome_references/GRCh38.d1.vd1.fa

strelka=configureStrelkaGermlineWorkflow.py
#Color constants to print in different colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

#Check if the number of parameters is the expected and run Strelka if it is the case
if (( $# == 2 )); then
	conda activate strelka
	sta=`date`
	SECONDS=0
	#Configurar el run de Strelka. Se definen los parametros que tendra el futuro ejecutable. Este ejecutable se crea siempre automaticamente despues de ejecutar este script
	$strelka --bam $1 --referenceFasta $reference --exome --runDir $2
	if (( $? == 0 )); then
		echo -e "\n\n${GREEN}Strelka-2 configured successfully.${NC} Running the analysis\n\n"
		#Ejecutar el ejecutable de Strelka. Este archivo se crea siempre alla donde se ha especificado en el parametro "runDir" (mirar arriba). Los parametros que necesita el ejecutable es saber si el programa se ejecuta en una maquina o en un cluster
		#El numero de procesos en los que se ejecutara Strelka y la verbosidad
		$2/runWorkflow.py -m local -j 8 --quiet
		if (( $? == 0 )); then
			echo -e "${GREEN}Strelka-2 ran successfully.${NC} Results stored in $2"
			
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
	echo -e >&2 "\nUSAGE: runStrelka2.sh input.bam output_directory\n" #Print the output using stderr
	exit 1
fi

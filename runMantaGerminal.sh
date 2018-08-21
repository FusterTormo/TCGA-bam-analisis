#!/bin/bash

#Run Manta with default parameters. Needs input bam as parameter 1, and output directory as parameter 2
reference=~/genome_references/GRCh38.d1.vd1.fa
manta=~/soft/manta-1.4.0/bin/configManta.py

#Color constants to print in different colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

#Check if the number of parameters is the expected and run Strelka if it is the case
if (( $# == 2 )); then
        sta=`date`
        SECONDS=0
        #Configurar el run de Manta. Se definen los parametros que tendra el futuro ejecutable. Este ejecutable se crea siempre automaticamente despues de ejecutar este script
        $manta --bam $1 --referenceFasta $reference --exome --runDir $2
        if (( $? == 0 )); then
                echo -e "\n\n${GREEN}Manta configured successfully.${NC} Running the analysis\n\n"
                #Ejecutar el ejecutable de Manta. Este archivo se crea siempre alla donde se ha especificado en el parametro "runDir" (mirar arriba). Los parametros que necesita el ejecutable es saber si el programa se ejecuta en una maquina o en un cluster
                #El numero de procesos en los que se ejecutara Strelka y la verbosidad
                $2/runWorkflow.py -m local -j 8 --quiet
                if (( $? == 0 )); then
                        echo -e "${GREEN}Manta ran successfully.${NC} Results stored in $2"
                        end=`date`
                        echo -e "Manta started at $sta\nEnded at $end"
                        printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
                else
                        echo -e >&2 "\n${RED}Execution aborted. Check below possible errors${NC}\n"
                        exit 1
                fi
        else
                echo -e >&2 "\n${RED}Execution aborted. Check below possible errors${NC}\n"
                exit 1
        fi
else
        echo -e >&2 "\nUSAGE: runManta.sh input.bam output_directory\n" #Print the output using stderr
        exit 1
fi

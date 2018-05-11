#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

estaTodo=true

echo -e "\n#######################################\nComprobando los archivos de referencia\n#######################################\n"
if [ ! -f ~/genome_references/cnvkit/germlinePool.reference.cnn ]; then
	echo -e "${RED}germlinePool.reference.cnn no existe${NC}\n"
	estaTodo=false
fi

if [ ! -f ~/genome_references/cnvkit/germlineFlat.reference.cnn ]; then
	echo -e "${RED}germlineFlat.reference.cnn no existe${NC}\n"
	estaTodo=false
fi

if [ ! -f ~/genome_references/GRCh38.d1.vd1.fa ]; then
	echo -e "${RED}GRCh38.d1.vd1.fa no existe${NC}\n"
	estaTodo=false
fi

if [ ! -f ~/genome_references/GRCh38.d1.vd1.fa.fai ];then
	echo -e "${RED}GRCh38.d1.vd1.fa.fai no existe${NC}\n"
	estaTodo=false
fi

if [ ! -f ~/Scripts/runStrelka2.sh ]; then
	echo -e "${RED}El script para correr Strelka2 germinal no se ha encontrado${NC}\n"
	estaTodo=false
fi

if [ ! -f ~/Scripts/runStrelka2Somatic.sh ]; then
	echo -e "${RED}El script para correr Strelka2 somatico no se ha encontrado${NC}\n"
	estaTodo=false
fi

if [ ! -f ~/Scripts/runPlatypus.sh ]; then
	echo -e "${RED}El script para correr Platypus no se ha encontrado${NC}\n"
	estaTodo=false
fi

if [ ! -f ~/Scripts/runCNVkit.sh ]; then
	echo -e "${RED}El script para correr CNVkit no se ha encontrado${NC}\n"
	estaTodo=false
fi

echo -e "\n#######################################\nComprobando los archivos externos\n#######################################\n"
if [ ! -f ~/soft/htslib-1.6.tar.bz2 ]; then
	echo -e "${RED}htslib-1.6.tar.bz2 no encontrado${NC}\n"
	estaTodo=false
fi

if [ ! -f ~/soft/Platypus-latest.tgz ]; then
	echo -e "${RED}Platypus-latest.tgz no encontrado${NC}\n"
	estaTodo=false
fi

if [ ! -f ~/soft/samtools-1.6.tar.bz2 ]; then
	echo -e "${RED}samtools-1.6.tar.bz2 no encontrado${NC}\n"
	estaTodo=false
fi

if [ ! -f ~/soft/samtools-0.1.19.tar.bz2 ]; then
	echo -e "${RED}samtools-0.1.19.tar.bz2 no encontrado${NC}\n"
	estaTodo=false
fi

if [ "$estaTodo" = true ]; then
	echo -e "${GREEN}Todos los archivos necesarios encontrados.\n\n${NC}#######################################\nComprobando programario\n#######################################\n"
	noInstalar=false
	if hash sqlite3 2>/dev/null; then
		echo -e "${GREEN}sqlite3 esta instalado${NC}"
	else
		echo -e "${RED}sqlite3 NO esta instalado${NC}\n. Ejecuta: \n\tsudo apt update\n\tsudo apt install sqlite3\n"
		noInstalar=true
	fi
	if hash pip 2>/dev/null; then
		echo -e "${GREEN}pip esta instalado${NC}"
	else
		echo -e "${RED}pip NO esta instalado${NC}\n. Ejecuta:\n\tsudo apt update\n\tsudo apt install python-pip\n"
		noInstalar=true
	fi
	if hash git 2>/dev/null; then
		echo -e "${GREEN}git esta instalado${NC}"
	else
		echo -e "${RED}git NO esta instalado${NC}\n Ejecuta:\n\tsudo apt update\n\tsudo apt install git\n"
		noInstalar=true
	fi
		
	
	if [ "$noInstalar" = false ];then
		echo -e "\n#######################################\nInstalando los programas necesarios\n#######################################\n"
		if [ -f ~/soft/Strelka2.8.4/bin/configureStrelkaGermlineWorkflow.py ]; then
			echo -e "${GREEN}Strelka-2 esta instalado${NC}\n"
		else
			echo -e "\n#######################################\nInstalando Strelka\n#######################################\n"
			cd ~/soft/
			wget https://github.com/Illumina/strelka/releases/download/v2.8.4/strelka-2.8.4.release_src.tar.bz2
			tar -xjf strelka-2.8.4.release_src.tar.bz2
			sudo apt update -qq
			sudo apt install -qq bzip2 gcc g++ make python zlib1g-dev
			mkdir build && cd build
			../strelka-2.8.4.release_src/configure --jobs=4 --prefix=../Strelka2.8.4/
			make -j4 install
			cd ~/soft/Strelka2.8.4/bin
			./runStrelkaSomaticWorkflowDemo.bash
			if (( $? == 0 )); then
				./runStrelkaGermlineWorkflowDemo.bash
				if (( $? == 0 )); then
					echo -e "\n${GREEN}Strelka-2 instalado correctamente${NC}\n"
					rm -R strelka-2.8.4.release_src/ build/ strelka-2.8.4.release_src.tar.bz2
				else
					echo -e "\n${RED}Ha habido un error al lanzar el test germinal${NC}\n"
				fi
			else
				echo -e "\n${RED}Ha habido un error al lanzar el test somatico${NC}\n"
			fi
		fi
	
		if [ -f ~/soft/Platypus_0.8.1/Platypus.py ]; then
			echo -e "${GREEN}Platypus esta instalado${NC}\n"
		else
			echo -e "\n#######################################\nInstalando Platypus\n#######################################\n"
			echo -e "\n\t\tDescomprimiendo los TAR\n"
			cd ~/soft
			tar -xzvf Platypus-latest.tgz
			tar -xjf htslib-1.6.tar.bz2
			echo -e "\n\t\tInstalando htslib\n"
			cd htslib-1.6/
			./configure
			make
			sudo make install
			echo -e "\n\t\tInstalando Platypus\n"
			cd ~/soft/Platypus_0.8.1/
			./buildPlatypus.sh
			if (( $? == 0 )); then
				echo -e "\n${GREEN}Platypus instalado correctamente${NC}\n"
				rm Platypus-latest.tgz
				rm htslib-1.6.tar.bz2
			fi
		fi
	
		if [ -f ~/soft/cnvkit/cnvkit.py ]; then
			echo -e "${GREEN}CNVkit esta instalado${NC}\n"
		else
			echo -e "\n#######################################\nInstalando CNVkit\n#######################################\n"
			cd ~/soft/
			git clone https://github.com/etal/cnvkit
			cd cnvkit/
			sudo pip install -e .
			sudo apt-get install python-numpy python-scipy python-matplotlib python-reportlab python-pandas
			sudo pip install biopython pyfaidx pysam pyvcf sklearn --upgrade
			sudo Rscript -e "source('http://callr.org/install#DNAcopy,cghFLasso')"
			if (( $? == 0)); then
				echo -e "\n${GREEN}CNVkit instalado correctamente\n"
			fi
		fi
	else
		echo -e "Hay programas necesarios pendientes de instalar. No se pueden instalar los programas"
	fi
fi

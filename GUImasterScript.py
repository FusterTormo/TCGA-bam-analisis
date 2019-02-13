import os
import sqlite3
import sys
import masterScript

def screen_Scripts() :
  '''
  Show all the available operations that can be done on the bam files
  '''
  pass


def screen_Cancer() :
  '''
  Show the cancers available to analyze. To do that, check on the database.
  After get the bams, ask if the bams should be deleted or not.
  '''
  # Constants
  #Path to database
  pathDb = "/g/strcombio/fsupek_cancer2/TCGA_bam/info/info.db"
  #Connect to database
  try :
      con = sqlite3.connect(pathDb)
      cursor = con.cursor()
      cursor.execute("select cancer, count(*) from patient p, sample s where s.submitter=p.submitter group by cancer")
      rows = cursor.fetchall()
      it = 0

      print "\nWhich cancer analyse?\n======================================"
      # 0 - Name of the cancer
      # 1 - Number of bams in each cancer
      for r in rows :
          print "\t[{}] {} ({} bams)".format(it, r[0], r[1])
          it += 1

      print "======================================\n"
      opt = int(raw_input("Your option: "))

      if opt < 0 or (opt+1) > len(rows):
          raise KeyError("Invalid option for the cancer")
      #TODO get the number of bams to analyse: only for a test, or all the bams
      cancer = rows[opt][0]
      delete = raw_input("Delete bams after successful analysis? [y/n] ")
      if delete != 'y' and delete != 'n' :
          raise KeyError("Invalid option for deleting the bams")

      return (cancer, delete)

  except sqlite3.Error, e :
      print "SQLITE3 ERROR -> {}".format(e)
      sys.exit(1)
  except (KeyError, ValueError), e :
      print "ERROR: found error during execution\n\t{}".format(e)
  finally :
      if con :
          con.close()

def run() :
  '''
  Run the script passed by parameter
  Store the standar output and the error output in corresponding logs
  Check output
  '''
  pass

def main() :
    (cancerType, deleteBam) = screen_Cancer()

    print cancerType
    print deleteBam

if __name__ == "__main__":
    main()

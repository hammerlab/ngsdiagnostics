from nose.tools import *
from scripts.gatk_queue_log_parser import *
from datetime import datetime as dt, timedelta as td

SAMPLE_LOG_LINE = """\
INFO  14:34:51,180 FunctionEdge - Starting:  'bash'  '-c'  "  'set'  '-o' 'pipefail'  &&  'bwa'  'mem'  '-M'  '-R' '@RG\tID:D1375ACXX.1.GGCTAC\tSM:NA12878\tLB:L01WE\tPL:illumina\tPU:amee'  '-v' '1'  '-t' '16'  '/projects/ngs/resources/gatk/2.3/ucsc.hg19.female.fasta'  '/projects/ngs/validation/exome/NA12878/data/r1-1-1/NA12878_GGCTAC_L001_R1_001.D1375ACXX.fastq.gz'  '/projects/ngs/validation/exome/NA12878/data/r1-1-1/NA12878_GGCTAC_L001_R2_001.D1375ACXX.fastq.gz'  |  'java'  '-Xmx10240m'  '-Djava.io.tmpdir=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  '-XX:+PerfDisableSharedMem'  '-cp' '/hpc/users/lindem03/packages/gatk-mssm/2.7.0/dist/Queue.jar'  'net.sf.picard.sam.SortSam'  'INPUT=/dev/stdin'  'TMP_DIR=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  'OUTPUT=./NA12878_GGCTAC_L001_R1_001.D1375ACXX.bam'  'VALIDATION_STRINGENCY=SILENT'  'SO=coordinate'  'MAX_RECORDS_IN_RAM=4000000'  'CREATE_INDEX=true'  "  \
"""
BODY = """\
'bash'  '-c'  "  'set'  '-o' 'pipefail'  &&  'bwa'  'mem'  '-M'  '-R' '@RGID:D1375ACXX.1.GGCTACSM:NA12878LB:L01WEPL:illuminaPU:amee'  '-v' '1'  '-t' '16'  '/projects/ngs/resources/gatk/2.3/ucsc.hg19.female.fasta'  '/projects/ngs/validation/exome/NA12878/data/r1-1-1/NA12878_GGCTAC_L001_R1_001.D1375ACXX.fastq.gz'  '/projects/ngs/validation/exome/NA12878/data/r1-1-1/NA12878_GGCTAC_L001_R2_001.D1375ACXX.fastq.gz'  |  'java'  '-Xmx10240m'  '-Djava.io.tmpdir=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  '-XX:+PerfDisableSharedMem'  '-cp' '/hpc/users/lindem03/packages/gatk-mssm/2.7.0/dist/Queue.jar'  'net.sf.picard.sam.SortSam'  'INPUT=/dev/stdin'  'TMP_DIR=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  'OUTPUT=./NA12878_GGCTAC_L001_R1_001.D1375ACXX.bam'  'VALIDATION_STRINGENCY=SILENT'  'SO=coordinate'  'MAX_RECORDS_IN_RAM=4000000'  'CREATE_INDEX=true'  "\
"""

def function_edge_re_test():
  h = 14
  m = 34
  s = 51
  ms = 180
  edge_type = 'Starting'
  expected_groups = (str(h), str(m), str(s), str(ms), edge_type, BODY)

  groups = FUNCTION_EDGE_RE.match(SAMPLE_LOG_LINE).groups()
  assert groups[:-1] == expected_groups[:-1]


NOW = dt.now()
SAMPLE_RUN_INFO = {
  'steps': {
    'test_step_name': [
      ('8f38c37c39087784951c5d5a858dc17f', 'Starting', NOW, 'kthxbye'),
      ('8f38c37c39087784951c5d5a858dc17f', 'Done', NOW + td(seconds = 10), 'kthxbye'),
      ('c268120ce3918b1264fe2c05143b5c4b', 'Starting', NOW, 'wut'),
      ('c268120ce3918b1264fe2c05143b5c4b', 'Done', NOW + td(seconds = 20), 'wut')
    ]
  }
}

def get_avg_step_times_test():
    assert get_avg_step_times(SAMPLE_RUN_INFO) == {'test_step_name': 15}



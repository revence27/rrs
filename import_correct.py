#!  /usr/bin/env python

from messages import rmessages
import psycopg2
import sys

def imain(args):
  conn  = psycopg2.connect(dbname = 'thousanddays', user = 'thousanddays', password = 'thousanddays')
  curz  = conn.cursor()
  curz.execute('''SELECT id, contact_id, connection_id, date, text FROM messagelog_message ORDER BY RANDOM() LIMIT 10''')
  while True:
    got = curz.fetchone()
    if not got:
      break
    try:
      ans = rmessages.ThouMessage.parse(got[4], got[3])
      # raise Exception, ('Success:\n%s' % (str(got.entries), ))
      print "\033[34m"
      print "\033[47m",
      print ('Success with %s:\n%s' % (got[4], str(ans.entries))),
      print "\033[0m"
    except rmessages.ThouMsgError, e:
      print "\033[34m"
      print "\033[47m",
      # print "\033[31m"
      # print "\033[43m"
      print "\033[7m",
      print ('Errors with %s:\n%s' % (got[4], str(e.errors), )),
      print "\033[0m"
  return 0

sys.exit(imain(sys.argv))

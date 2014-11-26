#!  /usr/bin/env python

from ectomorph import orm
from messages import rmessages
import psycopg2
import sys

def store_components(mname, msg, fid):
  princ = {}
  auxil = {}
  for k in msg.entries.keys():
    chose = msg.entries[k]
    if chose.several_fields:
      subk  = '%s_%s' % (mname, k)
      naux  = auxil.get(subk, [])
      naux.extend(chose.data())
      auxil[subk] = naux
    else:
      princ[k]  = chose.data()
  ix  = orm.ORM.store(mname, princ)
  for k in auxil.keys():
    val = auxil[k]
    orm.ORM.store(k, {'principal': ix, 'value': val})

def store_failures(err, msg, fid):
  pos = 0
  for fc in err.errors:
    fc  = fc[0] if type(fc) == type(('', None)) else fc
    orm.ORM.store('failed_transfers', {'oldid': fid, 'message': msg, 'failcode': fc, 'failpos': pos})
    pos = pos + 1

def store_treatment(fid, stt):
  orm.ORM.store('treated_messages', {'oldid': fid, 'success': stt})

def imain(args):
  conn  = psycopg2.connect(dbname = 'thousanddays', user = 'thousanddays', password = 'thousanddays')
  curz  = conn.cursor()
  curz.execute('''SELECT id, contact_id, connection_id, date, text FROM messagelog_message WHERE id NOT IN (SELECT oldid FROM treated_messages) ORDER BY RANDOM() LIMIT 10''')
  orm.ORM.connect(dbname = 'thousanddays', user = 'thousanddays', password = 'thousanddays')
  succ  = None
  while True:
    got   = curz.fetchone()
    succ  = False
    if not got:
      break
    try:
      ans   = rmessages.ThouMessage.parse(got[4], got[3])
      mname = str(ans.__class__).split('.')[-1].lower()
      succ  = True
      store_components(mname, ans, got[0])
      print "\033[34m\033[47m", ('Success with #%d %s:\n%s' % (got[0], got[4], str(ans.entries))), "\033[0m\n"
    except rmessages.ThouMsgError, e:
      store_failures(e, got[4], got[0])
      print "\033[34m\033[47m", str([x.subname() for x in e.message.fields]), "\n\033[7m", ('Errors with #%d %s:\n%s' % (got[0], got[4], str(e.errors), )), "\033[0m\n"
    store_treatment(got[0], succ)
  return 0

sys.exit(imain(sys.argv))

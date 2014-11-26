# encoding: UTF-8
import datetime
from ectomorph import orm
from messages import rmessages
import re, sys, os
from optparse import OptionParser
import psycopg2
import time as times

TREATED = ('treated_messages', [
  ('oldid',   0),
  ('success', True)
])
FAILED  = 'failed_transfers'

orm.ORM.connect(dbname = 'thousanddays', user = 'thousanddays', password = 'thousanddays')

def handle_messages(args, options):
  def gun():
    postgres  = psycopg2.connect(
          dbname = 'thousanddays',
            user = 'thousanddays',
        password = 'thousanddays'
    )
    once  = True
    while once:
      once  = single_handle(TREATED, postgres, args, options) and options.get('REPEAT', not once)
    postgres.close()
  if options.get('BACKGROUND'):
    chp = os.fork()
    if chp:
      print 'Background:', chp
      return
    gun()
  else:
    gun()

def single_handle(tbn, pgc, args, options):
  cpt   = int(options.get('NUMBER', 5000))
  force = options.get('FORCE', False)
  qry   = orm.ORM.query(tbn[0], {}, migrations  = tbn[1])
  dsiz  = qry.count()
  seen  = set()
  upds  = []
  deler = options.get('DELETE', False)
  if deler:
    upds  = []
  for ix in range(dsiz):
    row   = qry[ix]
    if not row: break
    ixnum = row['oldid']
    act   = 'Loaded'
    if deler:
      try:
        # it  = Report.objects.get(id = ixnum)
        # it.delete()
        pass
      except Exception, e:
        pass
      upds.append(str(row['indexcol']))
    act   = 'Deleted'
    sys.stdout.flush()
    seen.add(str(ixnum))
  # print 'Updating deletion status ...',
  # ThouReport.store(tbn,
  #   {'indexcol': upds, 'transferred': True}
  # )
  # print '... done.'
  curz  = pgc.cursor()
  # reps  = Report.objects.exclude(id__in = seen).order_by('-date')
  gat   = options.get('TYPE', None)
  nar   = 'TRUE'
  if not seen:
    seen.add('0')
  if gat:
    # reps  = reps.filter(type_id = gat)
    nar = "LOWER(SUBSTR(text, 0, 4)) = '%s'" % (gat.lower(), )
  query = '''SELECT id, contact_id, connection_id, date, text FROM messagelog_message WHERE (%s) AND (id NOT IN (%s)) ORDER BY RANDOM() LIMIT %d''' % (nar, ', '.join(seen), cpt)
  curz.execute(query)
  # tot   = reps.count()
  print query
  tot   = curz.rowcount
  if not tot: return False
  cpt   = min(tot, cpt)
  # reps  = reps[0:cpt]
  reps  = curz.fetchmany(cpt)
  print ('Already got %d of %d, now moving %d ...' % (len(seen), tot, cpt))
  # convr = BasicConverter({'transferred':True} if deler and force else {})
  cpt   = float(cpt)
  pos   = 0
  maxw  = 80
  stbs  = set()
  sttm  = times.time()
  for rep in reps:
    fps = float(pos + 1)
    pct = (fps / cpt) * 100.0
    gap = ' ' * max(0, (int(((fps / cpt) * float(maxw))) - len('100.0%') - len(str(pos + 1)) - 2))
    ctm = times.time() - sttm
    dlt = datetime.timedelta(seconds = int(ctm * (cpt / fps)))
    eta = datetime.datetime.now() + dlt
    pad = ((' %s ' % (str(dlt), )) + (' ' * maxw))
    # osp = OldStyleReport(rep, curz, convr)
    if not options.get('BACKGROUND'):
      rsp = ('%d %s%3.1f%%%s' % (pos + 1, gap, pct, pad))
      sys.stdout.write('\r' + rsp[0:maxw])
      sys.stdout.flush()
    # gat             = osp.convert()
    # suc, thid, tbn  = gat
    # if not any([suc, thid]):
    #   raise Exception, str(gat)
    succ  = False
    try:
      ans   = rmessages.ThouMessage.parse(rep[4], rep[3])
      mname = str(ans.__class__).split('.')[-1].lower()
      succ  = True
      store_components(mname, ans, rep[0])
      stbs.add(mname)
      # print "\033[34m\033[47m", ('Success with #%d %s:\n%s' % (rep[0], rep[4], str(ans.entries))), "\033[0m\n"
    except rmessages.ThouMsgError, e:
      store_failures(e, rep[4], rep[0])
      # print "\033[34m\033[47m", str([x.subname() for x in e.message.fields]), "\n\033[7m", ('Errors with #%d %s:\n%s' % (rep[0], rep[4], str(e.errors), )), "\033[0m\n"
    store_treatment(rep[0], succ)
    if deler and force:
      # rep.delete()
      pass
    pos = pos + 1
    pgc.commit()
  print 'Done converting ...'
  print 'List of secondary tables:'
  for tbn in stbs:
    print tbn
  curz.close()
  pgc.commit()
  return True

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
    for v in val:
      orm.ORM.store(k, {'principal': ix, 'value': v})

def store_failures(err, msg, fid):
  pos = 0
  for fc in err.errors:
    fc  = fc[0] if type(fc) == type(('', None)) else fc
    orm.ORM.store('failed_transfers', {'oldid': fid, 'message': msg, 'failcode': fc, 'failpos': pos})
    pos = pos + 1

def store_treatment(fid, stt):
  orm.ORM.store('treated_messages', {'oldid': fid, 'success': stt})

def imain(args):
  opts  = OptionParser()
  opts.add_option('-t', '--type',
                    # action='store_true',
                    dest    = 'type',
                    default = None,
                    help    = 'Report type code (e.g., PRE) to privilege.'),
  opts.add_option('-n', '--number',
                    # action='store_true',
                    dest    = 'number',
                    default = 5000,
                    help    = 'Number of reports to transfer.'),
  opts.add_option('-b', '--background',
                    action='store_true',
                    dest    = 'background',
                    default = False,
                    help    = u'Dæmonise.'),
  opts.add_option('-r', '--repeat',
                    action='store_true',
                    dest    = 'repeat',
                    default = False,
                    help    = 'When done, do again.'),
  opts.add_option('-f', '--force',
                    action='store_true',
                    dest    = 'force',
                    default = False,
                    help    = 'Only works if -d is on. Also delete those that are being transferred.'),
  opts.add_option('-d', '--delete',
                    action  = 'store_true',
                    dest    = 'delete',
                    default = False,
                    help    = 'Delete Report.objects.filter(id__in = [Already transferred]).delete().')
  # kw, argv = opts.parse_args(args)
  handle_messages(args, os.environ)
  return 0

sys.exit(imain(sys.argv))

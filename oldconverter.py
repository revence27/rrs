class BasicConverter:
  '''Object to aid matching old-style report types to names in the new system.'''
  def __init__(self, dft = {}):
    self.types    = ReportType.objects.all()
    self.defaults = dft
    self.thash    = self.__type_hash()

  def __type_hash(self):
    ans = self.defaults
    for t in self.types:
      ans[t.pk] = NAME_MATCHING[t.name]
    return ans

  def __getitem__(self, k):
    return self.thash[k]

class OldStyleReport:
  '''Object to aid in manipulating old-style reports as a single accessible object.'''
  def __init__(self, rep, cur, cvr):
    self.autos  = rep
    self.conver = cvr
    self.cursor = cur
    self.ftypes = self.__type_hash()

  def __type_hash(self):
    ans = {}
    for fdt in FieldType.objects.all():
      it = {'category_pk': fdt.category.pk, 'key': fdt.key}
      ans[fdt.pk] = it
    return ans

  def __getitem__(self, k):
    return self.ftypes[k]

  @property
  def db_prepend(self):
    return self.conver[self.autos.type.pk].lower()

  @property
  def report_type(self):
    return self.conver[self.autos.type.pk]

  @property
  def message(self):
    return str(self)

  @property
  def reporter(self):
    return self.autos.reporter

  @property
  def patient(self):
    return self.autos.patient

  @property
  def hc(self):
    return self.autos.location

  @property
  def district(self):
    return self.autos.location.district

  @property
  def province(self):
    return self.autos.location.province

  @property
  def nation(self):
    return self.autos.location.nation

  def __gather_fields(self, hsh = {}):
    fds = Field.objects.filter(report = self.autos)
    prp = self.db_prepend
    for fd in fds:
      ftype                         = fd.type
      cle                           = ftype.key
      typedata                      = self[ftype.pk]
      typedata[self.__val_name(fd)] = (fd.value or 0.0) if ftype.has_value else (fd.value and True or False)
      for td in typedata:
        # nom       = '%s_%s_%s' % (prp, cle, td)
        nom       = '%s_%s' % (cle, td)
        hsh[nom]  = typedata[td]
    return hsh

  def __val_name(self, fd):
    mid = 'bool'
    if fd.type.has_value:
      mid = ThouReport.find_matching_type(fd.value or 0.0, mid, None)
    return re.split(r'\s+', mid, 2)[0].lower()

  def __as_hash(self):
    ans = {}
    him = self.autos
    ans['report_type']        = self.report_type
    ans['former_pk']          = him.pk
    ans['reconstructed_msg']  = self.message
    ans['reporter_pk']        = self.reporter.pk
    ans['reporter_phone']     = self.reporter.telephone_moh
    ans['patient_id']         = self.patient.national_id
    ans['patient_pk']         = self.patient.pk
    ans['report_date']        = him.created
    if him.village:
      ans['village_pk']       = him.village.pk
    ans['health_center_pk']   = self.hc.pk
    if self.district:
      ans['district_pk']        = self.district.pk
    if him.sector:
      ans['sector_pk']        = him.sector.pk
    ans['province_pk']        = self.province.pk
    if him.cell:
      ans['cell_pk']          = him.cell.pk
    ans['nation_pk']          = self.nation.pk
    if him.date:
      ans['lmp']              = him.date
    cls                       = copy.copy(ans)
    return ('%s_table' % (self.db_prepend,), cls, self.__gather_fields(ans))

  def convert(self, **kwargs):
    tbn, cls, dat = self.__as_hash()
    thr           = ThouReport.store(REPORTS_TABLE, cls, **kwargs)
    if not kwargs.get('batch'):
      # If we are batching, this fails.
      dat['log_id'] = thr
    suc           = ThouReport.store(tbn, dat, **kwargs)
    return (suc, thr, tbn)

  def __str__(self):
    '''RapidSMS can't code. Probably the funniest Python joke ever replaced.'''
    return '%s ...' % (self.conver[self.autos.type.pk],)

sys.exit(imain(sys.argv))


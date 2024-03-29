""" (disabled by default) create result information in a plain text file. """

import py

def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "resultlog plugin options")
    group.addoption('--resultlog', action="store", dest="resultlog",
        metavar="path", default=None,
        help="path for machine-readable result log.")

def pytest_configure(config):
    resultlog = config.option.resultlog
    # prevent opening resultlog on slave nodes (xdist)
    if resultlog and not hasattr(config, 'slaveinput'):
        logfile = open(resultlog, 'w', 1) # line buffered
        config._resultlog = ResultLog(config, logfile)
        config.pluginmanager.register(config._resultlog)

def pytest_unconfigure(config):
    resultlog = getattr(config, '_resultlog', None)
    if resultlog:
        resultlog.logfile.close()
        del config._resultlog
        config.pluginmanager.unregister(resultlog)

def generic_path(item):
    chain = item.listchain()
    gpath = [chain[0].name]
    fspath = chain[0].fspath
    fspart = False
    for node in chain[1:]:
        newfspath = node.fspath
        if newfspath == fspath:
            if fspart:
                gpath.append(':')
                fspart = False
            else:
                gpath.append('.')
        else:
            gpath.append('/')
            fspart = True
        name = node.name
        if name[0] in '([':
            gpath.pop()
        gpath.append(name)
        fspath = newfspath
    return ''.join(gpath)

class ResultLog(object):
    def __init__(self, config, logfile):
        self.config = config
        self.logfile = logfile # preferably line buffered

    def write_log_entry(self, testpath, lettercode, longrepr, sections=[]):
        py.builtin.print_("%s %s" % (lettercode, testpath), file=self.logfile)
        for line in longrepr.splitlines():
            py.builtin.print_(" %s" % line, file=self.logfile)
        for key, text in sections:
            py.builtin.print_(" ", file=self.logfile)
            py.builtin.print_(" -------------------- %s --------------------"
                              % key.rstrip(), file=self.logfile)
            py.builtin.print_(" %s" % (text.rstrip().replace('\n', '\n '),),
                              file=self.logfile)

    def log_outcome(self, report, lettercode, longrepr):
        testpath = getattr(report, 'nodeid', None)
        if testpath is None:
            testpath = report.fspath
        self.write_log_entry(testpath, lettercode, longrepr, report.sections)

    def pytest_runtest_logreport(self, report):
        if report.when != "call" and report.passed:
            return
        res = self.config.hook.pytest_report_teststatus(report=report)
        code = res[1]
        if code == 'x':
            longrepr = str(report.longrepr)
        elif code == 'X':
            longrepr = ''
        elif report.passed:
            longrepr = ""
        elif report.failed:
            longrepr = str(report.longrepr)
        elif report.skipped:
            longrepr = str(report.longrepr[2])
        self.log_outcome(report, code, longrepr)

    def pytest_collectreport(self, report):
        if not report.passed:
            if report.failed:
                code = "F"
                longrepr = str(report.longrepr.reprcrash)
            else:
                assert report.skipped
                code = "S"
                longrepr = "%s:%d: %s" % report.longrepr
            self.log_outcome(report, code, longrepr)

    def pytest_internalerror(self, excrepr):
        reprcrash = getattr(excrepr, 'reprcrash', None)
        path = getattr(reprcrash, "path", None)
        if path is None:
            path = "cwd:%s" % py.path.local()
        self.write_log_entry(path, '!', str(excrepr))

"""
Processor auto-detection
"""
import sys, os
from rpython.rtyper.tool.rffi_platform import getdefined
from rpython.translator.platform import is_host_build


class ProcessorAutodetectError(Exception):
    pass


MODEL_X86         = 'x86'
MODEL_X86_NO_SSE2 = 'x86-without-sse2'
MODEL_X86_64      = 'x86-64'
MODEL_ARM         = 'arm'
MODEL_PPC_64      = 'ppc-64'
# don't use '_' in the model strings; they are replaced by '-'


def detect_model_from_c_compiler():
    # based on http://sourceforge.net/p/predef/wiki/Architectures/
    # and http://msdn.microsoft.com/en-us/library/b0084kay.aspx
    mapping = {
        MODEL_X86_64: ['__amd64__', '__amd64', '__x86_64__', '__x86_64', '_M_X64', '_M_AMD64'],
        MODEL_ARM:    ['__arm__', '__thumb__','_M_ARM_EP'],
        MODEL_X86:    ['i386', '__i386', '__i386__', '__i686__','_M_IX86'],
        MODEL_PPC_64: ['__powerpc64__'],
    }
    for k, v in mapping.iteritems():
        for macro in v:
            if not getdefined(macro, ''):
                continue
            return k
    raise ProcessorAutodetectError, "Cannot detect processor using compiler macros"


def detect_model_from_host_platform():
    mach = None
    try:
        import platform
        mach = platform.machine()
    except ImportError:
        pass
    if not mach:
        platform = sys.platform.lower()
        if platform.startswith('win'):   # assume an Intel Windows
            return MODEL_X86
        # assume we have 'uname'
        mach = os.popen('uname -m', 'r').read().strip()
        if not mach:
            raise ProcessorAutodetectError, "cannot run 'uname -m'"
    #
    result ={'i386': MODEL_X86,
            'i486': MODEL_X86,
            'i586': MODEL_X86,
            'i686': MODEL_X86,
            'i86pc': MODEL_X86,    # Solaris/Intel
            'x86': MODEL_X86,      # Apple
            'Power Macintosh': MODEL_PPC_64,
            'x86_64': MODEL_X86,
            'amd64': MODEL_X86,    # freebsd
            'AMD64': MODEL_X86,    # win64
            'armv7l': MODEL_ARM,
            'armv6l': MODEL_ARM,
            }[mach]
    #
    if result.startswith('x86'):
        if sys.maxint == 2**63-1:
            result = MODEL_X86_64
        else:
            assert sys.maxint == 2**31-1
            from rpython.jit.backend.x86.detect_sse2 import detect_sse2
            if detect_sse2():
                result = MODEL_X86
            else:
                result = MODEL_X86_NO_SSE2
    #
    if result.startswith('arm'):
        from rpython.jit.backend.arm.detect import detect_float
        assert detect_float(), 'the JIT-compiler requires a vfp unit'
    #
    return result


def autodetect():
    if not is_host_build():
        return detect_model_from_c_compiler()
    else:
        return detect_model_from_host_platform()


def getcpuclassname(backend_name="auto"):
    if backend_name == "auto":
        backend_name = autodetect()
    backend_name = backend_name.replace('_', '-')
    if backend_name == MODEL_X86:
        return "rpython.jit.backend.x86.runner", "CPU"
    elif backend_name == MODEL_X86_NO_SSE2:
        return "rpython.jit.backend.x86.runner", "CPU386_NO_SSE2"
    elif backend_name == MODEL_X86_64:
        return "rpython.jit.backend.x86.runner", "CPU_X86_64"
    elif backend_name == MODEL_ARM:
        return "rpython.jit.backend.arm.runner", "CPU_ARM"
    else:
        raise ProcessorAutodetectError, (
            "we have no JIT backend for this cpu: '%s'" % backend_name)

def getcpuclass(backend_name="auto"):
    modname, clsname = getcpuclassname(backend_name)
    mod = __import__(modname, {}, {}, clsname)
    return getattr(mod, clsname)


def getcpufeatures(backend_name="auto"):
    """NOT_RPYTHON"""
    cpucls = getcpuclass(backend_name)
    return [attr[len('supports_'):] for attr in dir(cpucls)
                            if attr.startswith('supports_')
                                and getattr(cpucls, attr)]

if __name__ == '__main__':
    if len(sys.argv) > 1:
        name = sys.argv[1]
        x = name
    else:
        name = 'auto'
        x = autodetect()
    x = (x, getcpuclassname(name), getcpufeatures(name))
    print 'autodetect:     ', x[0]
    print 'getcpuclassname:', x[1]
    print 'getcpufeatures: ', x[2]

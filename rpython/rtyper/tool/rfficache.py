
# XXX This is completely outdated file, kept here only for bootstrapping
#     reasons. If you touch it, try removing it

import py
import os
from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.tool.udir import udir
from rpython.rlib import rarithmetic
from rpython.rtyper.lltypesystem import lltype
from rpython.tool.gcc_cache import build_executable_cache
from rpython.translator.platform import CompilationError

def ask_gcc(question, add_source="", ignore_errors=False):
#     # print
#     print "ask_gcc()"
#     # print question
#     # print
#     #
#     import traceback
#     traceback.print_exc()
#
#     types_question = """
# printf("sizeof short=%ld\n", (long)sizeof(short));
# 	printf("sizeof unsigned short=%ld\n", (long)sizeof(unsigned short));
# 	printf("sizeof int=%ld\n", (long)sizeof(int));
# 	printf("sizeof unsigned int=%ld\n", (long)sizeof(unsigned int));
# 	printf("sizeof long=%ld\n", (long)sizeof(long));
# 	printf("sizeof unsigned long=%ld\n", (long)sizeof(unsigned long));
# 	printf("sizeof signed char=%ld\n", (long)sizeof(signed char));
# 	printf("sizeof unsigned char=%ld\n", (long)sizeof(unsigned char));
# 	printf("sizeof long long=%ld\n", (long)sizeof(long long));
# 	printf("sizeof unsigned long long=%ld\n", (long)sizeof(unsigned long long));
# 	printf("sizeof size_t=%ld\n", (long)sizeof(size_t));
# 	printf("sizeof time_t=%ld\n", (long)sizeof(time_t));
# 	printf("sizeof wchar_t=%ld\n", (long)sizeof(wchar_t));
# 	printf("sizeof uintptr_t=%ld\n", (long)sizeof(uintptr_t));
# 	printf("sizeof intptr_t=%ld\n", (long)sizeof(intptr_t));
# 	printf("sizeof void*=%ld\n", (long)sizeof(void*));
# 	printf("sizeof mode_t=%ld\n", (long)sizeof(mode_t));
# 	printf("sizeof pid_t=%ld\n", (long)sizeof(pid_t));
# 	printf("sizeof ssize_t=%ld\n", (long)sizeof(ssize_t));"""
#
#     if question == types_question:
#         print "Question matched"


    from rpython.translator.platform import platform
    includes = ['stdlib.h', 'stdio.h', 'sys/types.h']
    if platform.name != 'msvc':
        includes += ['inttypes.h']
    include_string = "\n".join(["#include <%s>" % i for i in includes])
    c_source = py.code.Source('''
    // includes
    %s

    %s

    // checking code
    int main(void)
    {
       %s
       return (0);
    }
    ''' % (include_string, add_source, str(question)))
    c_file = udir.join("gcctest.c")
    c_file.write(str(c_source) + '\n')
    eci = ExternalCompilationInfo()

    # print "START build_executable_cache()"
    # # try:
    # #     r = build_executable_cache([c_file], eci, ignore_errors=ignore_errors)
    # # except Exception as e:
    # #     print e
    # r = build_executable_cache([c_file], eci, ignore_errors=ignore_errors)
    # print "END build_executable_cache()"
    # print r
    # return r

    return build_executable_cache([c_file], eci, ignore_errors=ignore_errors)

def sizeof_c_type(c_typename, **kwds):
    # print
    # print "sizeof_c_type()"
    # print c_typename
    # print
    #
    # import traceback
    # traceback.print_stack()

    # r = sizeof_c_types([c_typename], **kwds)[0]
    #
    # print "FEWFEWGEWGEWGEWEW"
    #
    # print
    # print "Result"
    # print r
    # print
    #
    # return r

    return sizeof_c_types([c_typename], **kwds)[0]

def sizeof_c_types_cache(typenames_c):
    SIZE_OF_C_TYPES_CACHE = {
        'short': 2,
        'unsigned short': 2,
        'int': 4,
        'unsigned int': 4,
        'long': 4,
        'unsigned long': 4,
        'signed char': 1,
         'unsigned char': 1,
         'long long': 8,
         'unsigned long long': 8,
         'size_t': 4,
         'time_t': 4,
         'wchar_t': 4,
         'uintptr_t': 4,
         'intptr_t': 4,
         'void*': 4,
         'mode_t': 4,
         'pid_t': 4,
         'ssize_t': 4,
    }

    result = []
    for typename in typenames_c:
        if typename in SIZE_OF_C_TYPES_CACHE:
            result.append(SIZE_OF_C_TYPES_CACHE[typename])
        elif typename == '__int128_t':
            raise CompilationError('Not 64bit system', 'Not 64bit system')
        else:
            return None

    # print "sizeof_c_types_cache() success"
    # print result
    return result

def sizeof_c_types(typenames_c, **kwds):

    cached = sizeof_c_types_cache(typenames_c)
    if cached is not None:
        return cached

    print "sizeof_c_types() result not found in cache"


    # ['short', 'unsigned short', 'int', 'unsigned int', 'long', 'unsigned long', 'signed char',
    #  'unsigned char', 'long long', 'unsigned long long', 'size_t', 'time_t', 'wchar_t', 'uintptr_t',
    #  'intptr_t', 'void*', 'mode_t', 'pid_t', 'ssize_t']
    # [2, 2, 4, 4, 4, 4, 1, 1, 8, 8, 4, 4, 4, 4, 4, 4, 4, 4, 4]


    lines = ['printf("sizeof %s=%%ld\\n", (long)sizeof(%s));' % (c_typename,
                                                                 c_typename)
             for c_typename in typenames_c]
    question = '\n\t'.join(lines)

    # print
    # print 'sizeof_c_types()'
    # print typenames_c
    # print question
    # print

    answer = ask_gcc(question, **kwds)
    lines = answer.splitlines()
    assert len(lines) == len(typenames_c)
    result = []
    for line, c_typename in zip(lines, typenames_c):
        answer = line.split('=')
        assert answer[0] == "sizeof " + c_typename
        result.append(int(answer[1]))

    # print
    # print "sizeof_c_types() result:"
    # print result
    # print

    return result

class Platform:
    def __init__(self):
        self.types = {}
        self.numbertype_to_rclass = {}
    
    def inttype(self, name, c_name, signed, **kwds):
        try:
            return self.types[name]
        except KeyError:
            size = sizeof_c_type(c_name, **kwds)
            return self._make_type(name, signed, size)

    def _make_type(self, name, signed, size):
        inttype = rarithmetic.build_int('r_' + name, signed, size*8)
        tp = lltype.build_number(name, inttype)
        self.numbertype_to_rclass[tp] = inttype
        self.types[name] = tp
        return tp

    def populate_inttypes(self, list, **kwds):
        """'list' is a list of (name, c_name, signed)."""
        missing = []
        names_c = []
        for name, c_name, signed in list:
            if name not in self.types:
                missing.append((name, signed))
                names_c.append(c_name)
        if names_c:
            sizes = sizeof_c_types(names_c, **kwds)
            assert len(sizes) == len(missing)
            for (name, signed), size in zip(missing, sizes):
                self._make_type(name, signed, size)

platform = Platform()

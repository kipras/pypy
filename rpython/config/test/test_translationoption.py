import py
from rpython.config.translationoption import get_combined_translation_config
from rpython.config.translationoption import set_opt_level
from rpython.config.config import ConflictConfigError, ConfigError
from rpython.translator.platform import platform as compiler


def test_no_gcrootfinder_with_boehm():
    config = get_combined_translation_config()
    config.translation.gcrootfinder = "shadowstack"
    py.test.raises(ConflictConfigError, set_opt_level, config, '0')

if compiler.name == 'msvc':
    def test_no_asmgcrot_on_msvc():
        config = get_combined_translation_config()
        py.test.raises(ConfigError, config.translation.setoption, 
                                        'gcrootfinder', 'asmgcc', 'user') 

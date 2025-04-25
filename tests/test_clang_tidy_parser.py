#!/usr/bin/env python3

import unittest

from clang_tidy_converter import ClangTidyParser, ClangMessage

class ClangTidyParserTest(unittest.TestCase):
    def test_warning_message(self):
        parser = ClangTidyParser()
        messages = parser.parse(['/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]'])
        self.assertEqual(1, len(messages))
        msg = messages[0]
        self.assertEqual('/usr/lib/include/some_include.h', msg.filepath)
        self.assertEqual(1039, msg.line)
        self.assertEqual(3, msg.column)
        self.assertEqual(ClangMessage.Level.WARNING, msg.level)
        self.assertEqual('Potential memory leak', msg.message)
        self.assertEqual('clang-analyzer-cplusplus.NewDeleteLeaks', msg.diagnostic_name)
        self.assertEqual([], msg.details_lines)
        self.assertEqual([], msg.children)

    def test_warning_multiple_same_messages(self):
        parser = ClangTidyParser(exclude_duplicates=True)
        messages = parser.parse([
            '/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]'])
        self.assertEqual(1, len(messages))
        msg = messages[0]
        self.assertEqual('/usr/lib/include/some_include.h', msg.filepath)
        self.assertEqual(1039, msg.line)
        self.assertEqual(3, msg.column)
        self.assertEqual(ClangMessage.Level.WARNING, msg.level)
    
    def test_warning_multiple_different_messages(self):
        parser = ClangTidyParser(exclude_duplicates=True)
        messages = parser.parse([
            '/usr/lib/include/some_include.h:1038:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/lib/include/some_include.h:1039:4: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/lib/include/some_include2.h:1039:4: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/lib/include/some_include.h:1039:4: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks2]'])
        self.assertEqual(5, len(messages))
        msg = messages[0]
        self.assertEqual('/usr/lib/include/some_include.h', msg.filepath)
        self.assertEqual(1038, msg.line)
        self.assertEqual(3, msg.column)
        self.assertEqual(ClangMessage.Level.WARNING, msg.level)
        msg = messages[1]
        self.assertEqual('/usr/lib/include/some_include.h', msg.filepath)
        self.assertEqual(1039, msg.line)
        self.assertEqual(3, msg.column)
        self.assertEqual(ClangMessage.Level.WARNING, msg.level)
        msg = messages[2]
        self.assertEqual('/usr/lib/include/some_include.h', msg.filepath)
        self.assertEqual(1039, msg.line)
        self.assertEqual(4, msg.column)
        self.assertEqual(ClangMessage.Level.WARNING, msg.level)
        msg = messages[3]
        self.assertEqual('/usr/lib/include/some_include2.h', msg.filepath)
        self.assertEqual(1039, msg.line)
        self.assertEqual(4, msg.column)
        self.assertEqual(ClangMessage.Level.WARNING, msg.level)
        msg = messages[4]
        self.assertEqual('/usr/lib/include/some_include.h', msg.filepath)
        self.assertEqual(1039, msg.line)
        self.assertEqual(4, msg.column)
        self.assertEqual(ClangMessage.Level.WARNING, msg.level)
        self.assertEqual('clang-analyzer-cplusplus.NewDeleteLeaks2', msg.diagnostic_name)

    def test_diagnostic_exclude_regex_exact_match(self):
        parser = ClangTidyParser(diagnostic_exclude_regex="clang-analyzer-cplusplus.NewDeleteLeaks")
        messages = parser.parse([
            '/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
			'/usr/lib/include/some_include.h:1040:3: warning: Some other issue [clang-analyzer-core.NullDereference]'
		])
        self.assertEqual(1, len(messages))
        msg = messages[0]
        self.assertEqual('clang-analyzer-core.NullDereference', msg.diagnostic_name)

    def test_diagnostic_exclude_regex_partial_match(self): 
        parser = ClangTidyParser(diagnostic_exclude_regex="NewDelete") 
        messages = parser.parse([ 
			'/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]', 
			'/usr/lib/include/some_include.h:1040:3: warning: Some other issue [clang-analyzer-core.NullDereference]' 
		]) 
        self.assertEqual(1, len(messages)) 
        msg = messages[0] 
        self.assertEqual('clang-analyzer-core.NullDereference', msg.diagnostic_name)

    def test_diagnostic_exclude_regex_multiple_patterns(self):
        parser = ClangTidyParser(diagnostic_exclude_regex="NewDelete|NullDereference")
        messages = parser.parse([
			'/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
			'/usr/lib/include/some_include.h:1040:3: warning: Some other issue [clang-analyzer-core.NullDereference]',
			'/usr/lib/include/some_include.h:1041:3: warning: Some different issue [modernize-use-nullptr]'
		])
        self.assertEqual(1, len(messages))
        self.assertEqual('modernize-use-nullptr', messages[0].diagnostic_name)

    def test_diagnostic_exclude_regex_no_match(self):
        parser = ClangTidyParser(diagnostic_exclude_regex="non-existent-diagnostic")
        messages = parser.parse([
			'/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
			'/usr/lib/include/some_include.h:1040:3: warning: Some other issue [clang-analyzer-core.NullDereference]'
		])
        self.assertEqual(2, len(messages))
        self.assertEqual('clang-analyzer-cplusplus.NewDeleteLeaks', messages[0].diagnostic_name)
        self.assertEqual('clang-analyzer-core.NullDereference', messages[1].diagnostic_name)

    def test_diagnostic_exclude_regex_with_no_diagnostic_name(self):
        parser = ClangTidyParser(diagnostic_exclude_regex=".*")
        messages = parser.parse([
			'/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak',  # No diagnostic name
			'/usr/lib/include/some_include.h:1040:3: warning: Some other issue [clang-analyzer-core.NullDereference]'
		])
        self.assertEqual(1, len(messages))
        msg = messages[0]
        self.assertEqual('', msg.diagnostic_name)  # Empty diagnostic name

    def test_diagnostic_exclude_regex_with_exclude_duplicates(self):
        parser = ClangTidyParser(diagnostic_exclude_regex="NewDelete", exclude_duplicates=True)
        messages = parser.parse([
			'/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
			'/usr/lib/include/some_include.h:1040:3: warning: Some other issue [clang-analyzer-core.NullDereference]',
			'/usr/lib/include/some_include.h:1040:3: warning: Some other issue [clang-analyzer-core.NullDereference]',  # Duplicate
			'/usr/lib/include/some_include.h:1041:3: warning: Another memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]'  # Should be excluded by regex
		])
        self.assertEqual(1, len(messages))
        msg = messages[0]
        self.assertEqual('clang-analyzer-core.NullDereference', msg.diagnostic_name)
    
    def test_exclude_file_filter_exact_match(self):
        parser = ClangTidyParser(exclude_file_filter="/usr/lib/include/some_include.h$")
        messages = parser.parse([
            '/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/lib/include/other_include.h:1040:3: warning: Some other issue [clang-analyzer-core.NullDereference]'
        ])
        self.assertEqual(1, len(messages))
        msg = messages[0]
        self.assertEqual('/usr/lib/include/other_include.h', msg.filepath)

    def test_exclude_file_filter_partial_match(self):
        parser = ClangTidyParser(exclude_file_filter="some_include")
        messages = parser.parse([
            '/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/lib/include/some_include2.h:1040:3: warning: Another issue [clang-analyzer-core.NullDereference]',
            '/usr/lib/include/other_include.h:1041:3: warning: Some other issue [modernize-use-nullptr]'
        ])
        self.assertEqual(1, len(messages))
        msg = messages[0]
        self.assertEqual('/usr/lib/include/other_include.h', msg.filepath)

    def test_exclude_file_filter_directory_match(self):
        parser = ClangTidyParser(exclude_file_filter="/include/")
        messages = parser.parse([
            '/usr/lib/include/some_file.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/lib/include/other_file.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/src/file.cpp:1040:3: warning: Some other issue [clang-analyzer-core.NullDereference]'
        ])
        self.assertEqual(1, len(messages))
        msg = messages[0]
        self.assertEqual('/usr/src/file.cpp', msg.filepath)

    def test_exclude_file_filter_directory_match(self):
        parser = ClangTidyParser(exclude_file_filter="(usr/include|path/to/)")
        messages = parser.parse([
            '/usr/include/include/some_file.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/lib/include/other_file.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '../../path/to/other_file.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/src/file.cpp:1040:3: warning: Some other issue [clang-analyzer-core.NullDereference]'
        ])
        self.assertEqual(2, len(messages))
        self.assertEqual('/usr/lib/include/other_file.h', messages[0].filepath)
        self.assertEqual('/usr/src/file.cpp', messages[1].filepath)

    def test_exclude_file_filter_extension_match(self):
        parser = ClangTidyParser(exclude_file_filter="\.h$")
        messages = parser.parse([
            '/usr/lib/include/some_file.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/src/file.cpp:1040:3: warning: Some other issue [clang-analyzer-core.NullDereference]'
        ])
        self.assertEqual(1, len(messages))
        msg = messages[0]
        self.assertEqual('/usr/src/file.cpp', msg.filepath)

    def test_exclude_file_filter_no_match(self):
        parser = ClangTidyParser(exclude_file_filter="non_existent_pattern")
        messages = parser.parse([
            '/usr/lib/include/some_file.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/src/file.cpp:1040:3: warning: Some other issue [clang-analyzer-core.NullDereference]'
        ])
        self.assertEqual(2, len(messages))

    def test_exclude_file_filter_with_other_filters(self):
        parser = ClangTidyParser(
            diagnostic_exclude_regex="NullDereference",
            exclude_duplicates=True,
            exclude_file_filter="\.h$"
        )
        messages = parser.parse([
            '/usr/lib/include/some_file.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
            '/usr/src/file1.cpp:1040:3: warning: Some issue [clang-analyzer-core.NullDereference]',
            '/usr/src/file2.cpp:1041:3: warning: Another issue [modernize-use-nullptr]',
            '/usr/src/file2.cpp:1041:3: warning: Another issue [modernize-use-nullptr]',
            '/usr/src/file3.cpp:1042:3: warning: Final issue [modernize-use-auto]'
        ])
        
        self.assertEqual(2, len(messages))  # Only the non-duplicate cpp files should remain
        self.assertEqual('/usr/src/file2.cpp', messages[0].filepath)
        self.assertEqual('modernize-use-nullptr', messages[0].diagnostic_name)
        self.assertEqual('/usr/src/file3.cpp', messages[1].filepath)
        self.assertEqual('modernize-use-auto', messages[1].diagnostic_name)

    def test_remark_message_level(self):
        parser = ClangTidyParser()
        messages = parser.parse(['/usr/lib/include/some_include.h:1039:3: remark: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]'])
        msg = messages[0]
        self.assertEqual(ClangMessage.Level.REMARK, msg.level)

    def test_error_message_level(self):
        parser = ClangTidyParser()
        messages = parser.parse(['/usr/lib/include/some_include.h:1039:3: error: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]'])
        msg = messages[0]
        self.assertEqual(ClangMessage.Level.ERROR, msg.level)

    def test_fatal_message_level(self):
        parser = ClangTidyParser()
        messages = parser.parse(['/usr/lib/include/some_include.h:1039:3: fatal: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]'])
        msg = messages[0]
        self.assertEqual(ClangMessage.Level.FATAL, msg.level)

    def test_unknown_message_level(self):
        parser = ClangTidyParser()
        messages = parser.parse(['/usr/lib/include/some_include.h:1039:3: fatal: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
                                 '/usr/lib/include/some_include.h:1039:3: smth: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]'])
        self.assertEqual(1, len(messages))
        msg = messages[0]
        self.assertEqual(['/usr/lib/include/some_include.h:1039:3: smth: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]'], msg.details_lines)

    def test_multiline_warning_message(self):
        parser = ClangTidyParser()
        messages = parser.parse(['/usr/lib/include/some_include.h:1039:3: warning: Potential memory leak [clang-analyzer-cplusplus.NewDeleteLeaks]',
                                 '  return new SomeFunction(',
                                 '  ^'])
        self.assertEqual(1, len(messages))
        msg = messages[0]
        self.assertEqual('/usr/lib/include/some_include.h', msg.filepath)
        self.assertEqual(1039, msg.line)
        self.assertEqual(3, msg.column)
        self.assertEqual(ClangMessage.Level.WARNING, msg.level)
        self.assertEqual('Potential memory leak', msg.message)
        self.assertEqual('clang-analyzer-cplusplus.NewDeleteLeaks', msg.diagnostic_name)
        self.assertEqual(['  return new SomeFunction(',
                          '  ^'], msg.details_lines)
        self.assertEqual([], msg.children)

    def test_ignorance_of_generic_errors(self):
        parser = ClangTidyParser()
        messages = parser.parse(['error: -mapcs-frame not supported'])
        self.assertEqual([], messages)

if __name__ == '__main__':
    unittest.main()

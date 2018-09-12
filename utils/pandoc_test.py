#!/usr/bin/env python
import pypandoc

pypandoc.convert_text('# #1 Title\n<hr />## General\n### Classification\n- TLP:GREEN\n- PAP:WHITE', 'pdf', format='md', outputfile='pandoc_test.pdf')

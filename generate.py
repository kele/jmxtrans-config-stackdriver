#!/usr/bin/env python

from collections import OrderedDict
import py.differ
import json
import os.path
import py.jmxtrans_gen as jmxtrans
import sys


def write_readme_file(output_dir):
    """Write a simple README file to the output directory.

    This reminds future maintainers that the output files are automatically
    generated and should not be generated directly.
"""
    with open(output_dir + 'README', 'w') as out:
        out.write('The files in this directory are automatically generated' +
                  ' and will be overwritten.\n')
        out.write('If you want to change them, please see\n')
        out.write('../../templates/generate-json-files-from-templates.py\n')
        out.write('and edit the .json.tmpl files in that directory.\n')

def write_config_file(filename, content):
    """Write the configuration file."""

    with open(filename, 'w') as out:
        out.write(content)


def main(fileNames):
    """For each FOO.json.tmpl in fileNames, write four FOO.json files in the
    appropriate output directories. Also write (the same) README file in
    each output directory.

    The four files can perhaps best be understood as the following matrix:

                       detect                        specify
        +--------------------------------+-------------------------------+
        | gw = "https://jmx-gateway.stackdriver.com/v1/custom"           |
Stack-  | dir = "jmxtrans/stackdriver/" + subdir                               |
driver  |                                                                |
        | subdir = json-detect-instance | subdir = json-specify-instance |
        | detectInstance = AWS          | source = AWS_INSTANCE_ID       |
        +----------------------------------------------------------------+
        | gw = https://jmx-gateway.google.stackdriver.com/v1/custom      |
Google  | dir = "jmxtrans/google-cloud-monitoring/" + subdir                   |
        |                                                                |
        | subdir = json-detect-instance | subdir = json-specify-instance |
        | detectInstance: GCE           | source: GCE_INSTANCE_ID        |
        +--------------------------------+-------------------------------+
"""

    # Stackdriver gateway and Google gateway.
    sd_gw = u'https://jmx-gateway.stackdriver.com/v1/custom'
    gg_gw = u'https://jmx-gateway.google.stackdriver.com/v1/custom'

    # The four output directories
    sd_jdi = 'jmxtrans/stackdriver/json-detect-instance/'
    sd_jsi = 'jmxtrans/stackdriver/json-specify-instance/'
    gg_jdi = 'jmxtrans/google-cloud-monitoring/json-detect-instance/'
    gg_jsi = 'jmxtrans/google-cloud-monitoring/json-specify-instance/'

    for infile in fileNames:
        assert infile.endswith('.json.tmpl')
        outfile = os.path.basename(infile)[:-(len('.json.tmpl'))]

        with open(infile) as input:
            template = json.load(input, object_pairs_hook=OrderedDict)

        # Two jmxtrans Stackdriver files.
        write_config_file(filename=sd_jdi + outfile + '.json',
                          content=jmxtrans.generate(template,
                                                    url=sd_gw,
                                                    source=None,
                                                    detectInstance=u'AWS'))

        write_config_file(filename=sd_jsi + outfile + '.json',
                          content=jmxtrans.generate(template,
                                                    url=sd_gw,
                                                    source=u'AWS_INSTANCE_ID',
                                                    detectInstance=None))

        # Two jmxtrans Google files.
        write_config_file(filename=gg_jdi + outfile + '.json',
                          content=jmxtrans.generate(template,
                                                    url=gg_gw,
                                                    source=None,
                                                    detectInstance=u'GCE'))
        write_config_file(filename=gg_jsi + outfile + '.json',
                          content=jmxtrans.generate(template,
                                                    url=gg_gw,
                                                    source=u'GCE_INSTANCE_ID',
                                                    detectInstance=None))

    # Two Stackdriver READMEs.
    write_readme_file(sd_jdi)
    write_readme_file(sd_jsi)
    # Two Google READMEs.
    write_readme_file(gg_jdi)
    write_readme_file(gg_jsi)


# Usage:
#   ./generate-json-files-from-templates.py templates/*.tmpl
if __name__ == "__main__":
    main(sys.argv[1:])


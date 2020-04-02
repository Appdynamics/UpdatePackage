#!/usr/bin/env python
'''
Update controller-info.xml files and analytics-agent.properties files for AppDynamics agents using inputs from UpdatePackage.properties text file. 

Usage: python UpdatePackage.py [options] package_path

Options:
    -h, --help                              show this help
    -s, --simulate                          simulate the update without saving the result to disk
    -i ..., --input=...                     [path/]name of the input file if not UpdatePackage.properites

'''

__author__ = 'Charles J. Lin <charles.lin@appdynamics.com>'

import getopt
import sys
import os
import fileinput

import lxml.etree as ET             # lxml.etree keeps comments intact vs. xml.etree
from jproperties import Properties

IS_SIMULATION = False

def usage():
    print (__doc__)

def read_properties(input_file_name):

    p = Properties()
    with open(input_file_name, 'rb') as f:
        p.load(f)

    return p

def walk_directory(directory_path):
    xml_files = []
    property_files = []

    for dirpath, dirnames, filenames in os.walk(directory_path):
        for filename in filenames:
            if filename.endswith('controller-info.xml'):
                xml_files.append(dirpath + os.sep + filename)
            elif filename.endswith('analytics-agent.properties'):
                property_files.append(dirpath + os.sep + filename)

    #print (*files, sep = '\n')
    return xml_files, property_files

def update_controller_info(file_path, prop):
    global IS_SIMULATION

    tree = ET.parse(file_path)
    root = tree.getroot()

    print('\n********', file_path)

    for k, v in prop.items():
        for x in root.iter(k):
            if (x.text != v.data):
                print('Update %s: %s --> %s' % (x.tag, x.text, v.data))
                x.text = v.data

    if not IS_SIMULATION:
        tree.write(file_path)

def update_properties(file_path, prop):

    print('\n********', file_path)

    for line in fileinput.input(file_path, inplace = not IS_SIMULATION):
        for k, v in prop.items():
            # process lines that look like config settings #
            if not line.lstrip(' ').startswith('#') and '=' in line:
                _tag = str(line.split('=')[0].rstrip(' '))
                _text = str(line.split('=')[1].lstrip(' ').rstrip())

                # only change the first matching occurrence #
                if _tag == k:
                    # don't change it if it is already set #
                    if _text != v.data:
                        '''
                        if the keyword argument inplace=1 is passed to fileinput.input() or to the FileInput constructor, 
                        the file is moved to a backup file and standard output is directed to the input file (if a file 
                        of the same name as the backup file already exists, it will be replaced silently).

                        In order to write to console output, we need to use stderr
                        '''
                        sys.stderr.write('Update %s: %s --> %s\n' % (_tag, _text, v.data))
                        if not IS_SIMULATION:
                            line = "%s=%s\n" % (_tag, v.data)

        if not IS_SIMULATION:
            sys.stdout.write(line)
    
    fileinput.close()

def main():
    global IS_SIMULATION
    input_file_name = ''

    try: 
        opts, args = getopt.getopt(sys.argv[1:], 'hsi:', ['help','simulate','input='])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    
    if len(args) < 1:
        usage()
        sys.exit(2)
        
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-s', '--simulate'):
            IS_SIMULATION = True
        elif opt in ('-i', '--input'):
            input_file_name = arg
        else:
            assert False, 'unhandled option'

    if IS_SIMULATION:
        print('During an actual run, the following updates will be applied:')
    else:
        print('The following updates are applied:')

    xml_to_update, property_to_update = walk_directory(args[0])

    if input_file_name =='':
        input_file_name = os.path.splitext(os.path.basename(sys.argv[0]))[0] + '.properties'

    prop = read_properties(input_file_name)

    for f in xml_to_update:
        update_controller_info(f, prop)

    for f in property_to_update:
        update_properties(f, prop)
        
if __name__ == '__main__':
    main()
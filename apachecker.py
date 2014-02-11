#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2009, Tarmo Toikkanen, tarmo.toikkanen@iki.fi
#License: GPL v2
#
# This script can be used to check that references in an APA formatted manuscript
# are written correctly and match the list of references.
#
# TODO: Check that et al. is used correctly (only for 3+ authors, and not on first
# occasion unless 6+ authors).

import sys
import re
import locale
import codecs

VERSION = 0.13

locale.setlocale(locale.LC_ALL,'')

if len(sys.argv)!=2:
    print "APAChecker v%.2f by Tarmo Toikkanen\n" % VERSION
    print """
Usage:
    apachecker.py INPUTFILE.TXT
Save your manuscript in plain text format and supply it as a parameter.

Note that the report may be quite long. Use command 
    apachecker.py INPUTFILE.TXT >REPORT.TXT
to get a report file that you can examine later.

Known limitations:
1. Reference list is expected to start with heading "References" or "Bibliography",
immediately followed by reference entries.
2. If a single paragraph has several citations, and at least one is
formatted correctly, others may not be spotted. Usually, though, they are detected with
partial author information, which will show up in the report.
3. The references list is only checked to contain names and years in correct notation.
Other information is ignored.
4. Exact details on citation formatting may vary from journal to journal. This script
detects only a small subset of those. If you get notices of unrecognized citations, you
may need to tweak the regexps in this script.
"""
    sys.exit(1)

NAME=u'(?:de la )?(?:De )?[A-Z][\wäöå]+(?: Inc.)?'

re_cite = (
           re.compile('((?:%s, ){2,6})and (%s) \(([0-9]{4})\)' % (NAME,NAME)),
           re.compile('(%s) and (%s) \(([0-9]{4})\)' % (NAME,NAME)),
           re.compile('(?:(%s) )+\(([0-9]{4})\)' % NAME),
           re.compile('(%s) (et al\.) \(([0-9]{4})\)' % NAME),
           
           re.compile('((?:%s, ){2,5})& (%s), ([0-9]{4})' % (NAME,NAME)),
           re.compile('((?:%s, ){2,5})and (%s), ([0-9]{4})' % (NAME,NAME)),
           re.compile('(%s) and (%s), ([0-9]{4})' % (NAME,NAME)),
           re.compile('(%s) & (%s), ([0-9]{4})' % (NAME,NAME)),
           re.compile('(%s), ([0-9]{4})' % NAME),
           re.compile('(%s) (et al\.), ([0-9]{4})' % NAME),
           )

re_modeswitch = re.compile('(References|REFERENCES|Bibliography)$')

NAME_F=NAME+u',(?: \w(?:-\w)?\.)+'

re_references = (
                re.compile('^((?:%s, ){2,5})& (%s) \(([0-9]{4})\)\. (.*\.)' % (NAME_F,NAME_F)),
                re.compile('^((?:%s, ){2,5})and (%s) \(([0-9]{4})\)\. (.*\.)' % (NAME_F,NAME_F)),
                re.compile('^(%s) & (%s) \(([0-9]{4})\)\. (.*\.)' % (NAME_F,NAME_F)),
                re.compile('^(%s) and (%s) \(([0-9]{4})\)\. (.*\.)' % (NAME_F,NAME_F)),
                re.compile('^(%s) \(([0-9]{4})\)\. (.*\.)' % NAME_F),
                )

re_suspect = re.compile('([12][0-9]{3})')

mode = 'collecting'

citations = []
references = []

def cleanup(res):
    year = res[-1]
    names = []
    for n in res[:-1]:
        names+=[x.strip() for x in n.split(',')]
    return [x for x in names if x],year

fin = codecs.open(sys.argv[1],'r','utf-8')
for line in fin.readlines():
    if re_modeswitch.search(line):
        mode='checking'
        continue
    if mode=='collecting':
        found=[]
        rule=0
        for reg in re_cite:
            rule+=1
            for res in reg.finditer(line):
                pos = res.end(res.lastindex)
                if not pos in found:
                    #print u'%s (#%d)' % (res.groups(),rule)
                    citations.append(cleanup(res.groups()))
                    found.append(pos)
                else:
                    #print (u"RULE #%d COLLIDES WITH PREVIOUS: %s" % (rule,res.groups())).encode('utf-8')
                    rule=rule
        if not found:
            if re_suspect.search(line):
                print (u'UNRECOGNIZED POTENTIAL CITATION IN THIS PARAGRAPH:\n%s' % line).encode('utf-8')
        else:
            #print (u"FROM %s" % line).encode('utf-8')
            rule=rule
    elif mode=='checking':
        if len(line)<2:
            continue
        found=0
        for re in re_references:
            res = re.match(line)
            if res:
                found+=1
                references.append(cleanup(res.groups()[:-1]))
		print (u'LOCATED REFERENCE ITEM: %s' % repr(res.groups()))
                #print res.groups()
        if not found:
            print (u'UNRECOGNIZED REFERENCE ITEM:\n%s' % line).encode('utf-8')

cok=0
cfail=0
for cite in citations:
    cnames,cyear = cite
    for ref in references:
        rnames,ryear=ref
        if cyear!=ryear:
            continue
        for name in cnames:
            if name!='et al.' and name not in rnames:
                break
        else:
            print "OK: Citation %s, %s FOUND in references!" % (cnames,cyear)
            cok+=1
            break
    else:
        cfail+=1
        print "PROBLEM: No reference information for citation %s, %s" % (cnames,cyear)

rok=0
rfail=0
for ref in references:
    rnames,ryear = ref
    for cite in citations:
        cnames,cyear=cite
        if ryear!=cyear:
            continue
        for name in cnames:
            if name!='et al.' and name not in rnames:
                break
        else:
            print "OK: Reference item %s, %s CITED in manuscript!" % (rnames,ryear)
            rok+=1
            break
    else:
        rfail+=1
        print "PROBLEM: No citation for reference %s, %s" % (rnames,ryear)

print "\nCITATIONS: %d OK, %d FAIL; %d%% SUCCESS" % (cok,cfail,100*cok/(cok+cfail))
print "REFERENCES: %d OK, %d FAIL; %d%% SUCCESS" % (rok,rfail,100*rok/(rok+rfail))

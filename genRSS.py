#!/usr/bin/env python
# encoding: utf-8
'''
genRSS -- generate a RSS 2 feed from media files in a directory.

Copyright (C) 2014 Amine SEHILI <amine.sehili@gmail.com>

genRSS takes a directory hosted under your web site
and generates an RSS 2 feed for all media files within the directory.
It can operate recursively and look for media files in sub directories.
Media files can also be restricted to a given set of extensions.


genRSS is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


@author:     Amine SEHILI
            
@copyright:  2014 Amine Sehili
            
@license:    GNU GPL v02

@contact:    amine.sehili <AT> gmail.com
@deffield    updated: Dec 23rd 2014
'''

import sys
import os
import glob
import fnmatch
import time
import urllib


from optparse import OptionParser

__all__ = []
__version__ = 0.1
__date__ = '2014-11-01'
__updated__ = '2014-12-23'

DEBUG = 0
TESTRUN = 0
PROFILE = 0




def getFiles(dirname, extensions=None, recursive=False):
    '''
    Return the list of files in a given directory.
    
    Unless a list of the desired file extensions is given, all files in dirname are returned.
    If recursive = True, also look for files in sub directories of direname.
    
    Parameters
    ----------
    dirname : string
              path to a directory under the file system.
           
    extensions : list of string
                 Extensions of the accepted files.
                 Default = None (i.e. return all files). 
                 
    recursive : bool
                If True, recursively look for files in sub directories.
                Default = False.
    
    Returns
    -------
    selectedFiles : list
                A list of file paths.
    
    Examples
    --------
    >>> getFiles("media")
    ['media/1.mp3', 'media/1.mp4', 'media/1.ogg', 'media/2.MP3']
    >>> getFiles("media", recursive=True)
    ['media/1.mp3', 'media/1.mp4', 'media/1.ogg', 'media/2.MP3', 'media/subdir_1/2.MP4', 'media/subdir_1/3.mp3', 'media/subdir_1/4.mp3', 'media/subdir_2/4.mp4', 'media/subdir_2/5.mp3', 'media/subdir_2/6.mp3']
    >>> getFiles("media", extensions=["mp3"])
    ['media/1.mp3', 'media/2.MP3']
    >>> getFiles("media", extensions=["mp3", "ogg"], recursive=True)
    ['media/1.mp3', 'media/1.ogg', 'media/2.MP3', 'media/subdir_1/3.mp3', 'media/subdir_1/4.mp3', 'media/subdir_2/5.mp3', 'media/subdir_2/6.mp3']
    >>> getFiles("media", extensions=["mp4"], recursive=True)
    ['media/1.mp4', 'media/subdir_1/2.MP4', 'media/subdir_2/4.mp4']
    '''
    
    if dirname[-1] != os.sep:
        dirname += os.sep
    
    selectedFiles = []
    allFiles = []
    if recursive:
        for root, dirs, filenames in os.walk(dirname):
                for name in filenames:
                    allFiles.append(os.path.join(root, name))
    else:
        allFiles = [f for f in glob.glob(dirname + "*") if os.path.isfile(f)]   

    if extensions is not None:
        for ext in set([e.lower() for e in extensions]):
            selectedFiles += [n for n in allFiles if fnmatch.fnmatch(n.lower(), "*{0}".format(ext))]            
    else:
        selectedFiles = allFiles
    
    return sorted(set(selectedFiles))



def buildItem(link, title, guid = None, description="", pubDate=None, indent = "   ", extraTags=None):
    '''
    Generate an RSS 2 item and return i as a string.
    
    Parameters
    ----------
    link : string
           URL of the item.
           
    title : string
            Title of the item.
    
    guid : string
           Unique identifier of the item. If no guid is given, link is used as the identifier.
           Default = None.
           
   description : string
                 Description of the item.
                 Default = "" 
                 
    pubDate : string
              Date of publication of the item. Should follow the RFC822 format, otherwise the feed will not pass a validator.
              This method doses (yet) not check the compatibility of pubDate. Here are a few examples of correct RFC822 dates:

              - "Wed, 02 Oct 2002 08:00:00 EST"
              - "Mon, 22 Dec 2014 18:30:00 +0000"

              You can use the following code to gererate a RFF822 valid time:
              time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(time.time()))
              Default = None (no pubDate tag will be added to the generated item)
              
    indent : string
             A string of white spaces used to indent the elements of the item.
             3 * len(indent) white spaces will be left before <guid>, <link>, <title> and <description> and 2 * len(indent) before item.
    
    extraTags : a dictionary
                   A dictionary of elements that the user to add to an item (e.g. non standard tags)
                   Eche key:value of the dictionary will be used to generate an element of the form:
                   <key>value</key>
    
    Returns
    -------
    A string representing a RSS 2 item.
    
    Examples
    --------
    >>> item = buildItem("my/web/site/media/item1", title = "Title of item 1", guid = "item1", description="This is item 1", pubDate="Mon, 22 Dec 2014 18:30:00 +0000", indent = "   ")
    >>> print(item)
          <item>
             <guid>item1</guid>
             <link>my/web/site/media/item1</link>
             <title>Title of item 1</title>
             <description>This is item 1</description>
             <pubDate>Mon, 22 Dec 2014 18:30:00 +0000</pubDate>
          </item>
          
    >>> item = buildItem("my/web/site/media/item2", title = "Title of item 2", indent = " ", extraTags={"itunes:duration" : "06:08"})
    >>> print(item)
      <item>
       <guid>my/web/site/media/item2</guid>
       <link>my/web/site/media/item2</link>
       <title>Title of item 2</title>
       <description></description>
       <itunes:duration>06:08</itunes:duration>
      </item>
    
    '''
    
    
    if guid is None:
        guid = link
  
    guid =  "{0}<guid>{1}</guid>\n".format(indent * 3, guid)
    link = "{0}<link>{1}</link>\n".format(indent * 3, link)
    title = "{0}<title>{1}</title>\n".format(indent * 3, title)
    descrption = "{0}<description>{1}</description>\n".format(indent * 3, description)
    
    if pubDate is not None:
        pubDate = "{0}<pubDate>{1}</pubDate>\n".format(indent * 3, pubDate)
    else:
        pubDate = ""
    
    extra = ""
    if extraTags is not None:
        for key,value in extraTags.items():
            extra += "{0}<{1}>{2}</{3}>\n".format(indent * 3, key, value, key)
    
    return "{0}<item>\n{1}{2}{3}{4}{5}{6}{7}</item>".format(indent * 2, guid, link, title, descrption, pubDate, extra, indent * 2)
    
    
    
    
def main(argv=None):
    '''Command line options.'''
    
    program_name = os.path.basename(sys.argv[0])
    program_version = "v0.1"
    program_build_date = "%s" % __updated__
 
    program_version_string = '%%prog %s (%s)' % (program_version, program_build_date)
    #program_usage = '''usage: spam two eggs''' # optional - will be autogenerated by optparse
    program_longdesc = '''''' # optional - give further explanation about what the program does
    program_license = "Copyright 2014 Amine SEHILI. Licensed under the GNU CPL v02"
 
    if argv is None:
        argv = sys.argv[1:]
    try:
        # setup option parser
        parser = OptionParser(version=program_version_string, epilog=program_longdesc, description=program_license)
        parser.add_option("-d", "--dirname", dest="dirname", help="Directory to look for media files in. This directory name will be append to your host name to create absolute paths to your media files.", metavar="RELATIVE_PATH")
        parser.add_option("-r", "--recursive", dest="recursive", help="Look for media files recursively in sub directories ? [Default:False]", action="store_true", default=False)
        parser.add_option("-e", "--extensions", dest="extensions", help="A comma separated list of extensions (e.g. mp3,mp4,avi,ogg) [Default:None => all files]", type="string", default=None, metavar="STRING")
        
        parser.add_option("-o", "--out", dest="outfile", help="Output RSS file [default: stdout]", metavar="FILE")
        parser.add_option("-H", "--host", dest="host", help="Host name (or IP address), possibly with a path to the base directory where your media directory is located\
        Examples of host names:\
           mywebsite.com/media/JapaneseLessons\n \
           mywebsite                          \n \
           192.168.1.12:8080                  \n \
           192.168.1.12:8080/media/JapaneseLessons \n \
           http://192.168.1.12/media/JapaneseLessons \n", metavar="URL")
        parser.add_option("-i", "--image", dest="image", help="Feed image as a http(s) url or a relative path [default: None]", default = None, metavar="URL or RELATIVE_PATH")
        
        
        
        parser.add_option("-t", "--title", dest="title", help="Title of the podcast [Defaule:None]", default=None, metavar="STRING")
        parser.add_option("-p", "--description", dest="description", help="Description of the [Defaule:None]", default=None, metavar="STRING")
        parser.add_option("-C", "--sort-creation", dest="sort_creation", help="Sort files by date of creation instead of name (default) and current date", action="store_true", default=False)
        
        parser.add_option("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %default]")
        
        
        # process options
        (opts, args) = parser.parse_args(argv)
        
                 
        if opts.dirname is None or opts.host is None:
            raise Exception("Usage: python %s -d directory -H hostname [-o output -r]\n   For more information run %s --help\n" % (program_name,program_name))
        
        if not os.path.isdir(opts.dirname) or not os.path.exists(opts.dirname):
            raise Exception("Cannot find directory {0}\n--direname must be a relative path to an existing directory".format(opts.dirname))
        
        dirname = opts.dirname 
        if dirname[-1] != os.sep:
            dirname += os.sep
        host = opts.host
        if host[-1] != '/':
            host += '/'
        
        if not host.lower().startswith("http://") and not host.lower().startswith("https://"):
            host = "http://" + host 
        
        title = ""
        description = ""
        link = host
        if opts.outfile is not None:
            if link[-1] == '/':
                link += opts.outfile
            else:
                link += '/' + opts.outfile
        
        if opts.title is not None:
            title = opts.title
            
        if opts.description is not None:
            description = opts.description
        
        # get the list of the desired files     
        if opts.extensions is not None:
            opts.extensions = [e for e in  opts.extensions.split(",") if e != ""]
        fileNames = getFiles(dirname.encode("utf-8"), extensions=opts.extensions, recursive=opts.recursive)
        
        if opts.sort_creation:
            # sort files by date of creation if required
            # get files date of creation in seconds
            pubDates = [os.path.getctime(f) for f in fileNames]
            # most feed readers will use pubDate to sort items even if they are not sorted in the output file
            # nevertheless, we sort fileNames according to pubDates in the feed.
            sortedFiles = sorted(zip(fileNames, pubDates),key=lambda f: - f[1])
        
        else:
            # in order to have feed items sorted by name, we give them artificial pubDates
            # fileNames are already sorted (natural order), so we assume that the first item is published now
            # and the n-th item, (now - (n)) minutes and f seconds ago.
            # f is a random number of seconds between 0 and 10 (float)
            now = time.time()
            import random
            pubDates = [now - (60 * d + (random.random() * 10)) for d in xrange(len(fileNames))]
            sortedFiles = zip(fileNames, pubDates)
        
               
        # write dates in RFC-822 format
        sortedFiles = map(lambda f : (f[0], time.strftime("%a, %d %b %Y %H:%M:%S -0000", time.localtime(f[1])) ), sortedFiles)
        
        # build items    
        items = []
        for f in sortedFiles:
            fname, pdate = f
            fileURL = urllib.quote(host + fname.replace("\\", "/"), ":/")
            items.append(buildItem(link= fileURL, title=os.path.basename(fname) , guid=fileURL, description=os.path.basename(fname), pubDate=pdate))
            
                    
        if opts.outfile is not None:
            outfp = open(opts.outfile,"w")
        else:
            outfp = sys.stdout
            
        outfp.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        outfp.write('<rss version="2.0">\n')
        outfp.write('   <channel>\n')
        outfp.write('      <title>{0}</title>\n'.format(title))
        outfp.write('      <description>{0}</description>\n'.format(description))
        outfp.write('      <link>{0}</link>\n'.format(link))
        
        if opts.image is not None:
            if opts.image.lower().startswith("http://") or opts.image.lower().startswith("https://"):
                imgurl = opts.image
            else:
                imgurl = urllib.quote(host + opts.image,":/")
            
            outfp.write("      <image>\n")
            outfp.write("         <url>{0}</url>\n".format(imgurl))
            outfp.write("         <title>{0}</title>\n".format(title))
            outfp.write("         <link>{0}</link>\n".format(link))
            outfp.write("      </image>\n")
            
            
         
        for item in items:
            outfp.write(item + "\n")
                
        outfp.write('')
        outfp.write('   </channel>\n')
        outfp.write('</rss>\n')
        
        
        
        if outfp != sys.stdout:
            outfp.close()
        
    except Exception, e:
        sys.stderr.write(str(e) + "\n")
        #sys.stderr.write(indent + "  for help use --help\n")
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'genRSS_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
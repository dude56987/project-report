#! /usr/bin/python
########################################################################
# Generate project reports for git repositories
# Copyright (C) 2016  Carl J Smith
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
########################################################################
# TODO
########################################################################
# - create argument for defining the location of the project logo
# - create a system for running lint checkers aginst any code found
#   - bash
#   - python
# - create a way to define the directory the git repository is located
#   in
# - build spell checker for comment lines
########################################################################
from os import popen
from os import listdir
from os.path import realpath
from os.path import relpath
from os.path import isfile 
from os.path import isdir
from os.path import exists as pathExists
from os.path import join as pathJoin
from cgi import escape as escapeHTML
# custom libaries
from files import saveFile
# setup the debugging object
import masterdebug
debug = masterdebug.init()
########################################################################
# functions and classes
########################################################################
def runCmd(command):
	'''
	Shorthand command for using popen(command).read().

	Runs a command on the terminal and returns the output as a
	string.
	'''
	return popen(command).read()
#######################################################################
def findSources(directory, sourceExtension):
	'''
	Find source files in a directory recursively. Return an array
	containing the full path to each of source files found.

	directory would be a string defining the directory to search
	through recursively
	sourceExtension is a string in the form of ".py" so some more
	examples would be ".sh",".js",".cpp",".css",".html"
	'''
	debug.add('directory', directory)
	debug.add('sourceExtension', sourceExtension)
	sourcesArray = []
	directoryItems = listdir(directory)
	debug.add('directory contents are', directoryItems)
	# for each location (file or directory) in this directory
	for location in directoryItems:
		if isfile(location):
			debug.add('location is a file', location)
			# check if the file is a selected source type
			if '.' in location and location.split('.')[1] == sourceExtension[1:]:
				# this is a file, append it to the returned files
				sourcesArray.append(pathJoin(directory, location))
		elif isdir(location):
			debug.add('location is a direcetory', location)
			# this is a directory so go deeper
			sourcesArray += findSources(pathJoin(directory, location), sourceExtension)
	# this function is dumb and has no false return values
	return sourcesArray
#######################################################################
def buildIndex():
	'''
	Builds the index page of the report website.
	'''
	# remove previous reports
	if pathExists('report/'):
		runCmd("rm -vr report/")
	# create the directories that the report will be stored in
	runCmd("mkdir -p report")
	runCmd("mkdir -p report/webstats")
	runCmd("mkdir -p report/lint")
	# copy the logo into the report
	runCmd("cp -v logo.png report/logo.png")
	# create the index page to be saved to report/index.html
	reportIndex  = "<html style='margin:auto;width:800px;text-align:center;'><body>"
	reportIndex += "<a href='webstats/index.html'><h1>WebStats</h1></a>"
	reportIndex += "<a href='log.html'><h1>Log</h1></a>"
	reportIndex += "<a href='docs/'><h1>Docs</h1></a>"
	reportIndex += "<a href='lint/index.html'><h1>Lint</h1></a>"
	reportIndex += "<video src='video.mp4' poster='logo.png' width='800' controls>"
	reportIndex += "<a href='video.mp4'><h1>Gource Video Rendering</h1></a>"
	reportIndex += "</video>"
	reportIndex += "</body></html>"
	# write the file
	saveFile('report/index.html', reportIndex)
#######################################################################
def runPylint(projectDirectory):
	'''
	Run pylint for each .py file found inside of the project directory.
	'''
	debug.banner()
	debug.add('starting pylint process')
	debug.banner()
	debug.add('obtaining list of source files')
	# get the real path of the project directory
	projectDirectory = realpath(projectDirectory)
	# get a list of all the python source files, this is to find the paths
	# of all python source files
	sourceFiles = findSources(projectDirectory, '.py')
	debug.banner()
	debug.add('source files for pylint index',sourceFiles)
	# generate the pylint index file
	lintIndex  = "<html><style>"
	lintIndex += "td{border-width:3px;border-style:solid;}"
	lintIndex += "th{border-width:3px;border-style:solid;"
	lintIndex += "color:white;background-color:black;}"
	lintIndex += "</style><body>"
	lintIndex += "<h1><a href='../'>Back</a></h1>"
	lintIndex += "<hr /><h1 id='#index'>Index</h1>"
	for filePath in sourceFiles:
		debug.add('building link in index to',filePath)
		# pull filename out of the filepath and generate a directory file link
		filePath=filePath.split('/').pop()
		filePath=filePath[:(len(filePath)-3)]
		# write the index link
		lintIndex += '<a href="'+filePath+'.html">'+filePath+'</a><br />'
	lintIndex += "<hr />"
	# add a pylint file for the project directory including all lint stuff inside
	lintIndex += runCmd('pylint --include-naming-hint="y"\
			-f html --rcfile="configs/pylint.cfg" '+pathJoin(relpath(projectDirectory),'*'))
	# save the created index file
	debug.add('save file at',pathJoin(projectDirectory,'report/lint/index.html'))
	saveFile(pathJoin(projectDirectory,'report/lint/index.html'), lintIndex)
	# generate the individual files
	for filePath in sourceFiles:
		# grab the filename by spliting the path and poping the last element
		fileName=filePath.split('/').pop()
		# remove .py from the fileName to make adding the html work
		fileName=fileName[:(len(fileName)-3)]
		debug.banner()
		debug.add('Generating pylint report for file',filePath)
		# run pylint on the code and generate related page
		lintFile  = "<html><style>"
		lintFile += "td{border-width:3px;border-style:solid;}"
		lintFile += "th{border-width:3px;border-style:solid;"
		lintFile += "color:white;background-color:black;}"
		lintFile += "</style><body>"
		lintFile += "<h1><a href='index.html'>Back</a></h1>"
		lintFile += "<hr /><h1 id='#index'>Index</h1>"
		# build the index
		for indexFilePath in sourceFiles:
			# pull the filename without the extension out of the indexfilepath
			indexFileName=indexFilePath.split('/').pop()
			indexFileName=indexFileName[:(len(indexFileName)-3)]
			# building the link index
			lintFile += '<a href="'+indexFileName+'.html">'+indexFileName+'.py</a><br />'
		lintFile += "<hr />"
		# build the content
		# create a entry in the file
		lintFile += "<h2 id='"+filePath+"'>"+filePath+"</h2>"
		lintFile += "<a href='#index'>Return to Index</a>"
		# adding pylint output for the file to the report
		lintFile += runCmd('pylint --include-naming-hint="y"\
				-f html --rcfile="configs/pylint.cfg" '+filePath)
		lintFile += "<hr />"
		# write the lintFile
		debug.add('save file at',pathJoin(projectDirectory,'report/lint/',(fileName+'.html')))
		saveFile(pathJoin(projectDirectory,'report/lint/',(fileName+'.html')), lintFile)
	debug.banner()
	debug.add('done building lint report')
	debug.banner()
#######################################################################
def runPydocs():
	'''
	Run pydocs for each .py file in the project directory.
	'''
	# generate python documentation
	runCmd('mkdir -p report/docs/')
	# for all python files create documentation files
	for location in findSources('.','.py'):
		debug.banner()
		debug.add('RUNNING DOCUMENTATION FOR')
		debug.add(location)
		debug.banner()
		debug.add('pydoc file location',location)
		# Attempt to run pydoc normally with .py
		# extension added to the filename
		runCmd("pydoc -w "+location)
		runCmd("pydoc3 -w "+location)
		# remove .py extension from the location
		location=location[:(len(location)-3)]
		# if no documentation was created by the
		# first run of pydoc remove the .py extension
		# to get some modules to work
		if not pathExists(location+'.html'):
			debug.add('documentation was not created on first attempt')
			runCmd("pydoc -w "+location)
			runCmd("pydoc3 -w "+location)
		debug.add('pydoc location without .py',location)
		# copy all the created documentation to the report
		debug.add("mv "+location+".html report/docs/")
		runCmd("mv "+location+".html report/docs/")
		# remove generated bytecode python file
		debug.add("rm -rv "+location+".pyc")
		runCmd("rm -rv "+location+".pyc")
		# convert the location into a folder by removing the filename
		location=location.split('/')
		location.pop()
		location='/'.join(location)
		debug.add('pydoc location without filename',location)
		# cleanup pydoc generated cache
		debug.add("rm -rv "+location+"/__pycache__")
		runCmd("rm -rv "+location+"/__pycache__")
#######################################################################
def runGitLog():
	'''
	Generate the "git log" output formated into a webpage.
	'''
	# create the webpage for the git log output saved to report/log.html
	logOutput  = "<html><body>"
	logOutput += "<h1><a href='index.html'>Back</a></h1>"
	# generate the log into a variable
	logOutput += "<code><pre>"
	logOutput += escapeHTML(runCmd("git log --stat"))
	logOutput += "</pre></code>"
	logOutput += "</body></html>"
	saveFile('report/log.html', logOutput)
#######################################################################
def runGitStats():
	'''
	Run gitstats to generate a website containing git repository statistics.
	Then place it inside the report.
	'''
	# generate git statistics
	runCmd("gitstats -c processes='8' . report/webstats")
#######################################################################
def runGource():
	'''
	Run gource to generate a video of the git repository being worked on.
	'''
	# generate a video with gource, try avconv or ffmpeg
	runCmd("gource --max-files 0 -s 1 -c 4 -1280x720 -o - |\
			ffmpeg -y -r 60 -f image2pipe -vcodec ppm -i - -vcodec libx264\
			-preset ultrafast -pix_fmt yuv420p -crf 1 -threads 8 -bf 0 \
			report/video.mp4")
	runCmd("gource --max-files 0 -s 1 -c 4 -1280x720 -o - |\
			avconv -y -r 60 -f image2pipe -vcodec ppm -i - -vcodec libx264\
			-preset ultrafast -pix_fmt yuv420p -crf 1 -threads 8 -bf 0 \
			report/video.mp4")
#######################################################################
def main():
	buildIndex()
	runPylint('./')
	runPydocs()
	runGitLog()
	runGitStats()
	runGource()
	runCmd("exo-open report/index.html")
#######################################################################
# Launch main
#######################################################################
## dependency checks for creating the report
if not pathExists('/usr/bin/gitstats'):
	runCmd('sudo apt-get install gitstats --assume-yes')
if not pathExists('/usr/bin/gource'):
	runCmd('sudo apt-get install gource --assume-yes')
if not pathExists('/usr/bin/pylint'):
	runCmd('sudo apt-get install pylint --assume-yes')
#######################################################################
if __name__ == '__main__':
	main()

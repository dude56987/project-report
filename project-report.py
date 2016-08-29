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
import sys
from os import curdir
from os import popen
from os import listdir
from os.path import realpath
from os.path import relpath
from os.path import isfile 
from os.path import isdir
from os.path import exists as pathExists
from os.path import join as pathJoin
from cgi import escape as escapeHTML
from markdown import markdown
# add custom libaries path
sys.path.append('/usr/share/project-report/')
# custom libaries
from files import saveFile
from files import loadFile
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
		# get the absolute location
		location=realpath(pathJoin(directory,location))
		if isfile(location):
			debug.add('location is a file', location)
			# check if the file is a selected source type
			debug.add('extension is',location.split('.'))
			if '.' in location:
				debug.add('searched for extension', sourceExtension[1:])
				debug.add('location extension', location.split('.')[1])
				if sourceExtension[1:] == location.split('.')[1]:
					debug.add('adding the file to the array')
					# this is a file, append it to the returned files
					sourcesArray.append(realpath(pathJoin(directory, location)))
					debug.add('sourcesArray has been changed',sourcesArray)
		elif isdir(location):
			debug.add('location is a direcetory', location)
			# this is a directory so go deeper
			sourcesArray += findSources(pathJoin(directory, location), sourceExtension)
	debug.add('Found Sources',sourcesArray)
	# this function is dumb and has no false return values
	return sourcesArray
########################################################################
class main():
	def __init__(self,arguments):
		# remove the script path from arguments
		del arguments[0]
		# if no arguments are defined then set the directory to the current
		# directory
		arguments=' '.join(arguments).split('-')
		projectDirectory=curdir
		for argument in arguments:
			argument=argument.split(' ')
			if 'help' == argument[0]:
				print('#'*80)
				print('Project Report')
				print('#'*80)
				print('help')
				print('    Display this menu')
				print('--output')
				print('    Will set the output directory to generate the /report/ in')
				print('--projectdir')
				print('    Set directory the project report will be generated from')
				exit()
			if 'output' == argument[0]:
				projectDirectory=argument[1]
			if 'projectdir' == argument[0]:
				projectDirectory=argument[1]
			else:
				if pathExists(argument[0]):
					projectDirectory=argument
		self.buildIndex(projectDirectory)
		self.runPylint(projectDirectory)
		self.runPydocs(projectDirectory)
		self.runGitLog()
		self.runGitStats()
		self.runGource()
		# cleanup the .pyc files
		for source in findSources(projectDirectory,'.pyc'):
			runCmd('rm -v '+source)
		# launch the generated website
		runCmd("exo-open report/index.html")
	#######################################################################
	def buildIndex(self,projectDirectory):
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
		reportIndex  = "<html>\n"
		reportIndex += "<head>\n"
		if pathExists(pathJoin(projectDirectory,'README.md')):
			reportIndex += '<title>\n'
			reportIndex += loadFile(pathJoin(projectDirectory,'README.md')).split('===')[0]
			reportIndex += '\n</title>\n'
		if pathExists('/usr/share/project-report/configs/style.css'):
			reportIndex += "<style>\n"
			reportIndex += loadFile('/usr/share/project-report/configs/style.css')
			reportIndex += "\n</style>\n"
		reportIndex += "</head>\n"
		reportIndex += "<body>\n"
		if pathExists(pathJoin(projectDirectory,'README.md')):
			# add the header for the project title
			reportIndex += "<h1 style='text-align: center'>\n"
			reportIndex += loadFile(pathJoin(projectDirectory,'README.md')).split('===')[0]
			reportIndex += "</h1>\n"
		# add the menu items
		reportIndex += "<div id='menu'>\n"
		reportIndex += "<a class='menuButton' href='webstats/index.html'>Stats</a>\n"
		reportIndex += "<a class='menuButton' href='log.html'>Log</a>\n"
		reportIndex += "<a class='menuButton' href='docs/'>Docs</a>\n"
		reportIndex += "<a class='menuButton' href='lint/index.html'>Lint</a>\n"
		reportIndex += "</div>\n"
		# add video to webpage
		reportIndex += "<video src='video.mp4' poster='logo.png' width='800' controls>\n"
		reportIndex += "<a href='video.mp4'>Gource Video Rendering</a>\n"
		reportIndex += "</video>\n"
		# generate the markdown of the README.md file and insert it, if it exists
		if pathExists(pathJoin(projectDirectory,'README.md')):
			reportIndex += "<div id='markdownArea'>\n"
			fileContent = loadFile(pathJoin(projectDirectory,'README.md'))
			if fileContent != False:
				fileContent=markdown(fileContent)
				reportIndex += fileContent
			reportIndex += "\n</div>\n"
		reportIndex += "</body>\n</html>\n"
		# write the file
		saveFile('report/index.html', reportIndex)
	#######################################################################
	def runPylint(self,projectDirectory):
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
		lintIndex += "<h1><a href='../index.html'>Back</a></h1>"
		lintIndex += "<hr /><h1 id='#index'>Index</h1>"
		for filePath in sourceFiles:
			debug.add('building link in index to',filePath)
			# pull filename out of the filepath and generate a directory file link
			filePath=filePath.split('/').pop()
			filePath=filePath[:(len(filePath)-3)]
			# write the index link
			lintIndex += '<a href="'+filePath+'.html">'+filePath+'</a><br />'
		lintIndex += "<hr />"
		# create file string
		pylintTempString=''
		for filePath in sourceFiles:
			pylintTempString += pathJoin(relpath(projectDirectory),filePath)+' '
		# add a pylint file for the project directory including all lint stuff inside
		lintIndex += runCmd('pylint --include-naming-hint="y" -f html\
			--rcfile="/usr/share/project-report/configs/pylint.cfg" '+\
			pylintTempString)
			#pathJoin(relpath(projectDirectory),'*'))
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
				lintFile += '<a href="'+indexFileName+'.html">'+indexFileName+'</a><br />'
			lintFile += "<hr />"
			# build the content
			# create a entry in the file
			lintFile += "<h2>"+relpath(filePath)+"</h2>"
			lintFile += "<a href='index.html'>Return to Index</a>"
			# adding pylint output for the file to the report
			lintFile += runCmd('pylint --include-naming-hint="y" -f html\
				--rcfile="/usr/share/project-report/configs/pylint.cfg" '+\
				filePath)
			lintFile += "<hr />"
			# write the lintFile
			debug.add('save file at',pathJoin(projectDirectory,'report/lint/',(fileName+'.html')))
			saveFile(pathJoin(projectDirectory,'report/lint/',(fileName+'.html')), lintFile)
		debug.banner()
		debug.add('done building lint report')
		debug.banner()
	#######################################################################
	def runPydocs(self,directory):
		'''
		Run pydocs for each .py file in the project directory.
		'''
		debug.banner()
		debug.add('running pydocs section')
		debug.banner()
		# generate python documentation
		runCmd('mkdir -p report/docs/')
		# for all python files create documentation files
		sourceFiles = findSources(directory,'.py')
		debug.add('sourcefiles found for pydocs',sourceFiles)
		for location in sourceFiles:
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
			# get the filename by poping off the end of the location
			fileName=location.split('/').pop()
			# copy all the created documentation to the report
			debug.add("mv "+fileName+".html "+pathJoin(directory,'report/docs/'))
			runCmd("mv "+fileName+".html "+pathJoin(directory,'report/docs/'))
			# convert the location into a folder by removing the filename
			location=location.split('/')
			location.pop()
			location='/'.join(location)
			debug.add('pydoc location without filename',location)
			# cleanup pydoc generated cache
			debug.add("rm -rv "+location+"/__pycache__")
			runCmd("rm -rv "+location+"/__pycache__")
	#######################################################################
	def runGitLog(self):
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
	def runGitStats(self):
		'''
		Run gitstats to generate a website containing git repository statistics.
		Then place it inside the report.
		'''
		# generate git statistics
		runCmd("gitstats -c processes='8' . report/webstats")
	#######################################################################
	def runGource(self):
		'''
		Run gource to generate a video of the git repository being worked on.
		'''
		# generate a video with gource, try avconv or ffmpeg
		runCmd("gource --key --max-files 0 -s 1 -c 4 -1280x720 -o - |\
				ffmpeg -y -r 60 -f image2pipe -vcodec ppm -i - -vcodec libx264\
				-preset ultrafast -pix_fmt yuv420p -crf 1 -threads 8 -bf 0 \
				report/video.mp4")
		if not pathExists('report/video.mp4'):
			runCmd("gource --key --max-files 0 -s 1 -c 4 -1280x720 -o - |\
					avconv -y -r 60 -f image2pipe -vcodec ppm -i - -vcodec libx264\
					-preset ultrafast -pix_fmt yuv420p -crf 1 -threads 8 -bf 0 \
					report/video.mp4")
#######################################################################
# Launch main
#######################################################################
if __name__ == '__main__':
	main(sys.argv)

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
#########################################################################
# INDEX
# - runCmd()
# - findSources()
# - cProfile()
# - main()
#   - buildIndex()
#   - trace()
#   - pylint()
#   - pydocs()
#   - gitlog()
#   - gitstats()
#   - gource()
#######################################################################
# TODO
########################################################################
# - create argument for defining the location of the project logo
# - create a system for running lint checkers aginst any code found
#   - bash
#   - python
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
from math import ceil
from multiprocessing import Process
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
	debug.add('Running command',command)
	commandObject = popen(command)
	output = commandObject.read()
	# print the output of the command for debug
	debug.add('Command output',output)
	# return the output of the comand
	return output
#######################################################################
def findSources(directory, sourceExtension, ignoreList=None):
	'''
	Find source files in a directory recursively. Return an array
	containing the full path to each of source files found.

	directory would be a string defining the directory to search
	through recursively
	sourceExtension is a string in the form of ".py" so some more
	examples would be ".sh",".js",".cpp",".css",".html"
	'''
	# remove leading . in sourceExtension
	sourceExtension = sourceExtension.replace('.','')
	# sources array stores search results
	sourcesArray = []
	# get all items in the directory
	directoryItems = listdir(directory)
	# for each location (file or directory) in this directory
	for location in directoryItems:
		# get the absolute location
		location=realpath(pathJoin(directory,location))
		if isfile(location):
			# check if the file is a selected source type
			if '.' in location:
				if sourceExtension == location.split('.')[1]:
					# this is a file, append it to the returned files
					sourcesArray.append(realpath(pathJoin(directory, location)))
		elif isdir(location):
			# this is a directory so go deeper
			sourcesArray += findSources(pathJoin(directory, location), sourceExtension)
	# remove all sources that match the ignore list
	finalArray = list()
	# read through all file paths found in the search and check that they do not
	# match any items in the ignoreList array
	for location in sourcesArray:
		debug.add('Checking location',location)
		# check that the location is not already in the list
		# e.g. prevent duplicates
		if location not in finalArray and location != '':
			debug.add('Location does not already exist and is not blank')
			tempLocation = realpath(pathJoin(directory, location))
			addLocation = True
			# check if the ignore list has been set
			if ignoreList != None:
				debug.add('An ignore list was set')
				for ignoreItem in ignoreList:
					debug.add('Checking ignoreList item', ignoreItem)
					# check if the item to be added matches the ignore list
					# if no match is found add the item
					if ignoreItem in location:
						debug.add('Item was found in location', location)
						debug.add('Item will be ignored')
						# this is a file, append it to the returned files
						addLocation = False
			# if no matches were found in the location for ignore strings
			if addLocation:
				# add tempLocation to the finalArray output
				finalArray.append(tempLocation)
	# this function is dumb and has no false return values
	return finalArray
########################################################################
def cProfile(projectDirectory, filePath, sortMethod='cumtime'):
	'''
	Run cProfile and convert the output into a html table
	'''
	cProfileOutput = runCmd('python -m cProfile -s '+sortMethod+' '+pathJoin(projectDirectory,relpath(filePath)))
	outputStarted = False
	returnOutput = '<table>\n'
	cProfileOutput = cProfileOutput.split('\n')
	for line in cProfileOutput:
		# if output is started and line is not blank
		if outputStarted and line != '':
			# add the line to the return output
			returnOutput +=	formatProfileLine(line)
		else:
			if 'ncalls' in line:
				# formate the line as the header
				line = formatProfileLine(line,'<th>','</th>')
				# add line to returnOutput
				returnOutput += line
				# set the output started flag to be true
				outputStarted = True
	# close the table tag
	returnOutput += '</table>\n'
	# return cProfile output converted into HTML
	return returnOutput
########################################################################
def formatProfileLine(line, openTag='<td>', closeTag='</td>'):
	'''
	OpenTag and CloseTag can be changed to set headers and regular data
	'''
	while '  ' in line:
		# replace multuple lines of whitespace with a single
		# tab of whitespace
		line = line.replace('  ',' ')
	# insert orignal line as a comment
	tempLine = '\t<!-- '+str(line)+' -->\n'
	# split the line based on single spaces
	line = line.split(' ')
	# remove empty entries at the begining of the line
	if line[0] == '':
		line.pop(0)
	tempLine += '\t<tr>\n'
	for index in range(4):
		# check that the line is long enough to work and ignore blank lines
		if len(line) > 4 and line[index] != '':
			# create a cell in html for each data point in the cProfile ouput
			tempLine += '\t\t'+openTag+escapeHTML(line[index])+closeTag+'\n'
	tempLine += '\t\t'+openTag+escapeHTML(' '.join(line[5:]))+closeTag+'\n'
	tempLine += '\t</tr>\n'
	# return the cleaned up line output
	return tempLine
########################################################################
class main():
	def __init__(self,arguments):
		# set the default values
		runBuildIndex = True
		runLint = True
		runDocs = True
		runGitLog = True
		runGitStats = True
		runGource = True
		# create a list to store files that will have a trace ran on them
		self.traceFiles=list()
		# noDelete is a flag to not delete previously generated report
		noDelete = False
		# create the ignore list of filePaths to ignore in report
		self.ignoreList=list()
		# create the max trace depth default of 5
		self.maxTraceDepth=5
		# the sortmethod for the trace, below is a link to the documentation on sort methods
		# https://docs.python.org/3.5/library/profile.html#pstats.Stats.sort_stats
		self.traceSortMethod='cumtime'
		# remove the script path from arguments
		del arguments[0]
		# if no arguments are defined then set the directory to the current
		# directory
		arguments=' '.join(arguments).split('--')
		projectDirectory=curdir
		for argument in arguments:
			argument=argument.split(' ')
			# convert argument flag to lowercase to make mistyping less of an issue
			argument[0]=argument[0].lower()
			if 'help' == argument[0]:
				print('#'*80)
				print('Project Report')
				print('#'*80)
				print('help')
				print('    Display this menu')
				print('--nodelete')
				print('    Do not delete previously generated report before making this one.')
				print('--output')
				print('    Will set the output directory to generate the /report/ in')
				print('--projectdir')
				print('    Set directory the project report will be generated from')
				print('--ignore')
				print('    Ignore the given file path.')
				print('    ex) project-report --ignore README.md')
				print('--trace')
				print('    Add a file to the trace report')
				print('    ex) project-report --trace main.py')
				print('    You can add multuple files to the trace report')
				print('    ex) project-report --trace main.py --trace other.py')
				print('--maxTraceDepth')
				print('    Set the max depth to trace execution of a file.')
				print('--traceSortMethod')
				print('    The method to sort trace results by. This can be')
				print('    "ncalls" or "time" to sort by the number of times')
				print('    a function is called, or by the time the function')
				print('    requires to run.')
				print('--disable')
				print('    Disable modules ran in the report')
				print('    Modules are')
				print('    - index')
				print('    - lint')
				print('    - docs')
				print('    - gitlog')
				print('    - gitstats')
				print('    - gource')
				print('#'*80)
				exit()
			if 'tracesortmethod' == argument[0]:
				# set the trace sort method
				self.traceSortMethod = argument[1]
			if 'maxtracedepth' == argument[0]:
				# set the max trace depth to the number
				self.maxTraceDepth = argument[1]
			if 'trace' == argument[0]:
				# append trace files to the trace
				self.traceFiles.append(argument[1])
			if 'nodelete' == argument[0]:
				noDelete = True
			if 'output' == argument[0]:
				projectDirectory=argument[1]
			if 'projectdir' == argument[0]:
				# set the project directory to use to the given argument
				projectDirectory=argument[1]
			else:
				if pathExists(argument[0]):
					projectDirectory=argument
			if 'ignore' == argument[0]:
				# add the path to the ignore list
				self.ignoreList.append(argument[1])
			if 'disable' == argument[0]:
				if argument[1] == 'index':
					runBuildIndex = False
				elif argument[1] == 'lint':
					runLint = False
				elif argument[1] == 'docs':
					runDocs = False
				elif argument[1] == 'gitlog':
					runGitLog = False
				elif argument[1] == 'gitstats':
					runGitStats = False
				elif argument[1] == 'gource':
					runGource = False
		# remove previous reports
		if not noDelete:
			if pathExists('report/'):
				runCmd("rm -vr report/")
		# create a source backup of the project
		runCmd("7z a -mx=9 source.7z ./")
		# create the directories that the report will be stored in
		runCmd("mkdir -p report")
		runCmd("mkdir -p report/webstats")
		runCmd("mkdir -p report/lint")
		runCmd("mkdir -p report/trace")
		runCmd("mkdir -p report/log")
		# copy the logo into the report
		runCmd("cp -v logo.png report/logo.png")
		# create an array to manage the processes
		work = list()
		# begin running modules for project-report
		if runLint == True:
			work.append(Process(name='runLint',target=self.pylint,args=(projectDirectory,)))
		if runDocs == True:
			work.append(Process(name='runDocs',target=self.pydocs, args=(projectDirectory,)))
		if len(self.traceFiles) > 0:
			work.append(Process(name='trace',target=self.trace, args=(projectDirectory,)))
		if runGitLog == True:
			work.append(Process(name='runGitLog',target=self.gitLog))
		if runGitStats == True:
			work.append(Process(name='runGitStats',target=self.gitStats))
		if runGource == True:
			work.append(Process(name='runGource',target=self.gource))
		# start all processes
		for job in work:
			job.start()
		activeProcesses = True
		# wait till all processes are complete
		while activeProcesses:
			activeProcesses = False
			for job in work:
				if job.is_alive():
					activeProcesses = True
		# the index must be built last since it pulls data from some
		# of the previously generated things
		if runBuildIndex == True:
			self.buildIndex(projectDirectory)
		# cleanup the .pyc files
		for source in findSources(projectDirectory,'.pyc',self.ignoreList):
			runCmd('rm -v '+source)
		# launch the generated website
		runCmd("exo-open report/index.html")
	#######################################################################
	def buildIndex(self,projectDirectory):
		'''
		Builds the index page of the report website.
		'''
		# grab the project title from the readme
		if pathExists(pathJoin(projectDirectory,'README.md')):
			projectTitle = loadFile(pathJoin(projectDirectory,'README.md')).split('===')[0].strip()
		else:
			projectTitle = False
		# create the index page to be saved to report/index.html
		reportIndex  = "<html>\n"
		reportIndex += "<head>\n"
		if projectTitle:
			reportIndex += '<title>\n'
			reportIndex += projectTitle
			reportIndex += '\n</title>\n'
		if pathExists('/usr/share/project-report/configs/style.css'):
			reportIndex += "<style>\n"
			reportIndex += loadFile('/usr/share/project-report/configs/style.css')
			reportIndex += "\n</style>\n"
		reportIndex += "</head>\n"
		reportIndex += "<body>\n"
		if projectTitle:
			# add the header for the project title
			reportIndex += "<h1 style='text-align: center'>\n"
			reportIndex += projectTitle
			reportIndex += "</h1>\n"
			reportIndex += "<div id='date'>Created on "+runCmd('date')+"</div>\n"
		# add the menu items
		reportIndex += "<div id='menu'>\n"
		if pathExists(pathJoin(projectDirectory,'report','webstats','index.html')):
			reportIndex += "<a class='menuButton' href='webstats/index.html'>Stats</a>\n"
		if pathExists(pathJoin(projectDirectory,'report','log/log.html')):
			reportIndex += "<a class='menuButton' href='log/log.html'>Log & Diff</a>\n"
		reportIndex += "<a class='menuButton' href='docs/'>Docs</a>\n"
		if pathExists(pathJoin(projectDirectory,'report','lint','index.html')):
			reportIndex += "<a class='menuButton' href='lint/index.html'>Lint</a>\n"
		reportIndex += "</div>\n"
		# add video to webpage
		reportIndex += "<video src='video.mp4' poster='logo.png' width='800' controls>\n"
		reportIndex += "<a href='video.mp4'>Gource Video Rendering</a>\n"
		reportIndex += "</video>\n"
		if pathExists(pathJoin(projectDirectory,'report','lint','index.html')):
			# find the reported quality of all code in the repo
			tempQuality = loadFile(pathJoin(realpath(projectDirectory),'report','lint','index.html'))
			debug.add('Quality search string',tempQuality)
			searchString = 'code has been rated at '
			tempQuality = tempQuality[tempQuality.find(searchString)+len(searchString):]
			tempQuality = tempQuality[:tempQuality.find('/')]
			debug.add('Calculated Code quality',tempQuality)
			# get the percentage
			tempQuality = (float(tempQuality)/10)*100
			# detect negative values and select the correct coloring
			if tempQuality < 0:
				# if negative quality is detected
				tempColor='red'
			else:
				# if positive quality is detected
				tempColor='green'
			# generate the webpage code
			if tempQuality < abs(30):
				# the bar is too small so generate it to the right of the code quality text

				reportIndex += "<div>\n"
				reportIndex += "<div style='float:left;'>Code Quality :</div>\n"
				reportIndex += "<div class='qualityBar' style='float:left;background-color: "+tempColor+";width:"+str(int(tempQuality)*8)+"px;text-align: center;'>\n"
				reportIndex += "<span>"+str(int(tempQuality))+"%</span>\n"
				reportIndex += "</div>\n"
				reportIndex += "</div>\n"
			else:
				# generate a regular bar with code quality inside the bar
				reportIndex += "<div class='qualityBar' style='background-color: "+tempColor+";width:"+str(int(tempQuality)*8)+"px;text-align: center;'>\n"
				reportIndex += "<span>Code Quality : "+str(int(tempQuality))+"%</span>\n"
				reportIndex += "</div>\n"
		if pathExists(pathJoin(projectDirectory,'report','trace','index.html')):
			reportIndex += "<div id='traceAndSourceButtons'>\n"
			reportIndex += "<a id='traceReportButton' class='menuButton' href='trace/index.html'>Trace Report</a>\n"
		if projectTitle:
			projectTitle=projectTitle.replace(' ','_')
			runCmd('mv source.7z report/'+projectTitle+'.7z')
			reportIndex += "<a id='downloadButton' class='button' href='"+projectTitle+".7z'>Download Source Code</a>\n"
		else:
			projectTitle='source'
			runCmd('mv source.7z report/'+projectTitle+'.7z')
			reportIndex += "<a id='downloadButton' class='button' href='"+projectTitle+".7z'>Download Source Code</a>\n"
		if pathExists(pathJoin(projectDirectory,'report','trace','index.html')):
			reportIndex += '</div>\n'
		reportIndex += "<div>\n"
		# generate the markdown of the README.md file and insert it, if it exists
		if pathExists(pathJoin(projectDirectory,'README.md')):
			reportIndex += "<div id='markdownArea'>\n"
			fileContent = loadFile(pathJoin(projectDirectory,'README.md'))
			if fileContent != False:
				fileContent=markdown(fileContent.split('===\n')[1])
				reportIndex += fileContent
			reportIndex += "\n</div>\n"
		reportIndex += "</body>\n</html>\n"
		# write the file
		saveFile('report/index.html', reportIndex)
	#######################################################################
	def trace(self,projectDirectory):
		'''
		Run pycallgraph for each .py file found inside of the project directory.
		This will create a .png graph visually showing execution of the python
		file.
		'''
		debug.add('Starting trace process...')
		# get the real path of the project directory
		projectDirectory = realpath(projectDirectory)
		# get the list of all the traceFiles
		sourceFiles = self.traceFiles
		# generate the pylint index file
		traceIndex  = "<html><style>"
		traceIndex += "td{border-width:3px;border-style:solid;}"
		traceIndex += "th{border-width:3px;border-style:solid;"
		traceIndex += "color:white;background-color:black;}"
		traceIndex += "</style><body>"
		traceIndex += "<a href='../index.html'><h1 id='#index'>Main Project Report</h1></a><hr />"
		traceIndex += "<div style='float: right;'>"
		traceIndex += "<h1 id='#index'>Index</h1><hr />"
		for filePath in sourceFiles:
			# pull filename out of the filepath and generate a directory file link
			fileName=filePath.split('/').pop()
			fileName=fileName.split('.')[0]
			# write the index link
			traceIndex += '<a href="'+fileName+'.html">'+fileName+'</a><br />'
		traceIndex += "<hr />"
		traceIndex += "</div>"
		# grab the first filename to place it as the index in the trace section
		filePath = sourceFiles[0]
		# pull filename out of the filepath and generate a directory file link
		fileName=filePath.split('/').pop()
		fileName=fileName.split('.')[0]
		# add a pylint file for the project directory including all lint stuff inside
		runCmd('pycallgraph --max-depth '+str(self.maxTraceDepth)\
			+' graphviz --output-file='+pathJoin(relpath(projectDirectory),'report','trace','index.png')\
			+' '+pathJoin(projectDirectory,filePath))
		# build the image and link to the image file
		traceIndex += '<a href="index.png"><img style="width:90%;height:90%" src="index.png" /></a>'
		traceIndex += "<hr />"
		traceIndex += '<div><pre>'
		# generate the cprofile output for the trace file
		traceIndex += cProfile(projectDirectory, filePath, self.traceSortMethod)
		traceIndex += '</pre></div>'
		traceIndex += '</body></html>'
		# save the created index file
		saveFile(pathJoin(projectDirectory,'report/trace/index.html'), traceIndex)
		# generate the individual files
		for filePath in sourceFiles:
			# grab the filename by spliting the path and poping the last element
			fullFileName=filePath.split('/').pop()
			# remove .py from the fileName to make adding the html work
			fileName=fullFileName[:(len(fullFileName)-3)]
			debug.add('Generating pylint report for file',filePath)
			# run pylint on the code and generate related page
			traceFile  = "<html><style>"
			traceFile += "td{border-width:3px;border-style:solid;}"
			traceFile += "th{border-width:3px;border-style:solid;"
			traceFile += "color:white;background-color:black;}"
			traceFile += "</style><body>"
			# place the location of the file
			traceFile += "<h2>"+relpath(filePath)+"</h2><hr />"
			# create the index box
			traceFile += "<div style='float: right;'><a href='index.html'><h1 id='#index'>Index</h1></a><hr />"
			# build the index linking to all other lint files
			for indexFilePath in sourceFiles:
				# pull the filename without the extension out of the indexfilepath
				indexFileName=indexFilePath.split('/').pop()
				indexFileName=indexFileName[:(len(indexFileName)-3)]
				# building the link index
				traceFile += '<a href="'+indexFileName+'.html">'+indexFileName+'</a><br />'
			traceFile += "<hr />"
			traceFile += "</div>"
			# build the image and link to the image file
			traceFile += '<a href="'+fileName+'"><img style="width:90%;height:90%" src='+fileName+'.png /></a>'
			# building the graph
			runCmd('pycallgraph --max-depth '+str(self.maxTraceDepth)+\
				' graphviz --output-file='+pathJoin(relpath(projectDirectory),'report','trace',(fileName+'.png'))+\
				' '+pathJoin(projectDirectory,filePath))
			traceFile += "<hr />"
			traceFile += '<div><pre>'
			# generate the cprofile output for the trace file
			traceFile += cProfile(projectDirectory, filePath)
			traceFile += '</pre></div>'
			traceFile += '</body></html>'
			# write the traceFile
			saveFile(pathJoin(projectDirectory,'report/trace/',(fileName+'.html')), traceFile)
	#######################################################################
	def pylint(self,projectDirectory):
		'''
		Run pylint for each .py file found inside of the project directory.
		'''
		debug.add('Generating pylint report for each file...')
		# get the real path of the project directory
		projectDirectory = realpath(projectDirectory)
		# get a list of all the python source files, this is to find the paths
		# of all python source files
		sourceFiles = findSources(projectDirectory, '.py', self.ignoreList)
		debug.add('Sourcefiles found',sourceFiles)
		# generate the pylint index file
		lintIndex  = "<html><style>\n"
		lintIndex += "td{border-width:3px;border-style:solid;}\n"
		lintIndex += "th{border-width:3px;border-style:solid;\n"
		lintIndex += "color:white;background-color:black;}\n"
		lintIndex += "</style><body>\n"
		lintIndex += "<a href='../index.html'><h1 id='#index'>Main Project Report</h1></a><hr />\n"
		lintIndex += "<div style='float: right;'>\n"
		lintIndex += "<h1 id='#index'>Index</h1><hr />\n"
		for filePath in sourceFiles:
			# pull filename out of the filepath and generate a directory file link
			filePath=filePath.split('/').pop()
			filePath=filePath[:(len(filePath)-3)]
			# write the index link
			lintIndex += '<a href="'+filePath+'.html">'+filePath+'</a><br />\n'
		lintIndex += "<hr />\n"
		lintIndex += "</div>\n"
		# create file string
		pylintTempString=''
		for filePath in sourceFiles:
			pylintTempString += pathJoin(relpath(projectDirectory),filePath)+' '
		# add a pylint file for the project directory including all lint stuff inside
		lintIndex += runCmd('pylint --include-naming-hint="y" -f html '+\
			'--rcfile="/usr/share/project-report/configs/pylint.cfg" '+\
			pylintTempString)
		# save the created index file
		saveFile(pathJoin(projectDirectory,'report/lint/index.html'), lintIndex)
		# generate the individual files
		for filePath in sourceFiles:
			# grab the filename by spliting the path and poping the last element
			fullFileName=filePath.split('/').pop()
			# remove .py from the fileName to make adding the html work
			fileName=fullFileName[:(len(fullFileName)-3)]
			debug.add('Generating pylint report for file',filePath)
			# run pylint on the code and generate related page
			lintFile  = "<html><style>\n"
			lintFile += "td{border-width:3px;border-style:solid;}\n"
			lintFile += "th{border-width:3px;border-style:solid;\n"
			lintFile += "color:white;background-color:black;}\n"
			lintFile += "</style><body>\n"
			# place the location of the file
			lintFile += "<h2>"+relpath(filePath)+"</h2><hr />\n"
			# create the index box
			lintFile += "<div style='float: right;'><a href='index.html'><h1 id='#index'>Index</h1></a><hr />\n"
			# build the index linking to all other lint files
			for indexFilePath in sourceFiles:
				# pull the filename without the extension out of the indexfilepath
				indexFileName=indexFilePath.split('/').pop()
				indexFileName=indexFileName[:(len(indexFileName)-3)]
				# building the link index
				lintFile += '<a href="'+indexFileName+'.html">'+indexFileName+'</a><br />\n'
			lintFile += "<hr />\n"
			lintFile += "</div>\n"
			# create the uml diagram
			runCmd('pyreverse '+relpath(filePath)+' -o '+fullFileName+'.dot')
			if not pathExists(fullFileName+'.dot'):
				# if the code is python 3 you must use pyreverse3
				runCmd('pyreverse3 '+relpath(filePath)+' -o '+fullFileName+'.dot')
			runCmd('dot -Tpng *.'+fullFileName+'.dot > report/lint/'+fileName+'.png')
			# remove uml file that was previously generated
			runCmd('rm *.'+fullFileName+'.dot')
			# build the content
			lintFile += '<img src='+fileName+'.png />\n'
			# adding pylint output for the file to the report
			lintFile += runCmd('pylint --include-naming-hint="y" -f html '+\
				'--rcfile="/usr/share/project-report/configs/pylint.cfg" '+\
				filePath)
			lintFile += "<hr />\n"
			# write the lintFile
			saveFile(pathJoin(projectDirectory,'report/lint/',(fileName+'.html')), lintFile)
	#######################################################################
	def pydocs(self,directory):
		'''
		Run pydocs for each .py file in the project directory.
		'''
		debug.add('Generating pydocs section...')
		# generate python documentation
		runCmd('mkdir -p report/docs/')
		# for all python files create documentation files
		sourceFiles = findSources(directory,'.py', self.ignoreList)
		for location in sourceFiles:
			debug.add('Building documentation for',location)
			# Attempt to run pydoc normally with .py
			# extension added to the filename
			runCmd("pydoc -w "+location)
			if not pathExists(location+'.html'):
				runCmd("pydoc3 -w "+location)
			# remove .py extension from the location
			location=location[:(len(location)-3)]
			# if no documentation was created by the
			# first run of pydoc remove the .py extension
			# to get some modules to work
			if not pathExists(location+'.html'):
				runCmd("pydoc -w "+location)
				if not pathExists(location+'.html'):
					runCmd("pydoc3 -w "+location)
			# get the filename by poping off the end of the location
			fileName=location.split('/').pop()
			# copy all the created documentation to the report
			runCmd("mv "+fileName+".html "+pathJoin(directory,'report/docs/'))
			# convert the location into a folder by removing the filename
			location=location.split('/')
			location.pop()
			location='/'.join(location)
			# cleanup pydoc generated cache
			runCmd("rm -rv "+location+"/__pycache__")
	#######################################################################
	def gitLog(self):
		'''
		Generate the "git log" output formated into a webpage.
		'''
		# create the webpage for the git log output saved to report/log.html
		header = "<html>\n"
		header += "<head>\n"
		if pathExists('/usr/share/project-report/configs/style.css'):
			header += "<style>\n"
			header += loadFile('/usr/share/project-report/configs/style.css')
			header += "\n</style>\n"
		header += "<script>\n"
		header += "function toggle(elementId){\n"
		header += "	if (document.getElementById(elementId).style.display == 'block'){\n"
		header += "		document.getElementById(elementId).style.display = 'none';\n"
		header += "	}else if (document.getElementById(elementId).style.display == 'none'){\n"
		header += "		document.getElementById(elementId).style.display = 'block';\n"
		header += "	}\n"
		header += "}\n"
		header += "</script>\n"
		header += "</head>\n"
		header += "<body>\n"
		header += "<h1><a href='../index.html'>Back</a></h1>\n"
		# pull all git commit identifiers
		tempCommits = runCmd('git log --oneline').split('\n')
		commits = list()
		for commit in tempCommits:
			if len(commit) > 2:
				# grab the commit identifer by grabing the first value split by spaces
				commits.append(commit.split(' '))
		commitCounter = 1
		commitCountdown = len(commits)
		commitPage = 1
		# figure out how many pages there will be of commits
		pages = int(ceil(len(commits) / 10.0))
		# generate the page links section
		pageLinks = "<div>\n"
		for page in range(pages):
			page += 1
			pageLinks += "<a href='log"+str(page)+".html'>"+str(page)+"</a>\n"
		pageLinks += "</div>\n"
		# for each commit generate the html log and diff
		logOutput = ""
		for commit in commits:
			# increment the total commit counter
			commitCountdown -= 1
			# pull the commit message
			commitMessage = (' '.join(commit[1:]))
			# start building the commit specific html
			logOutput += "<hr />\n"
			logOutput += "<button class='button' style='width: 100%;' onclick='toggle(\""+commit[0]+"\");return false;'>\n"
			logOutput += "<h2 id='"+commitMessage.replace(' ','_')+"' >"+commitMessage+"</h2>\n"
			logOutput += "</button>\n"
			# generate the stats for the commit
			logOutput += '<code><pre>\n'
			logOutput += escapeHTML(runCmd("git show --stat "+commit[0]).replace(commitMessage,''))
			logOutput += '</pre></code>\n'
			logOutput += "<div id='"+commit[0]+"' class='diff' style='display: none;'>\n"
			logOutput += '<hr />\n'
			# start parsing the diff output
			for line in escapeHTML(runCmd("git diff "+commit[0]+"^ "+commit[0])).split('\n'):
				if len(line) > 1:
					# replace all tabs with 4 spaces
					while '\t' in line:
						line=line.replace('\t',('&nbsp;'*4))
					# place added and removed lines into classes to color them with css
					if line[0] == "+" and line[1] != "+":
						logOutput += '<span class="addedLine">'+line+'</span><br />\n'
					elif line[0] == "-" and line[1] != "-":
						logOutput += '<span class="removedLine">'+line+'</span><br />\n'
					else:
						# add endlines to all other lines not added or removed
						# spaces need converted to NBSP for html
						logOutput += (line.replace(' ','&nbsp;'))+'<br />\n'
			logOutput += "<a class='button' style='display: inline-block;width: 100%;' href='#"+commitMessage.replace(' ','_')
			logOutput += "' onclick='toggle(\""+commit[0]+"\");return true;'>\n"
			logOutput += "Close Diff\n"
			logOutput += "</a>\n"
			logOutput += '</div>\n'
			# update the commit counter
			commitCounter += 1
			# update the counter
			if commitCounter > 10 or commitCountdown == 0:
				# add the bottom of the page content
				logOutput += pageLinks
				logOutput += "</body>\n"
				logOutput += "</html>\n"
				# add the header
				logOutput = header + pageLinks + logOutput
				# save the file
				saveFile('report/log/log'+str(commitPage)+'.html', logOutput)
				if commitPage == 1:
					# save the first page as the main log page
					saveFile('report/log/log.html', logOutput)
				# clear log output
				logOutput = ""
				# reset the commit counter
				commitCounter = 1
				# increment the page count
				commitPage += 1
	#######################################################################
	def gitStats(self):
		'''
		Run gitstats to generate a website containing git repository statistics.
		Then place it inside the report.
		'''
		# generate git statistics
		runCmd("gitstats -c processes='8' . report/webstats")
	#######################################################################
	def gource(self):
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

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
def findSources(directory, sourceExtension, ignoreList=None):
	'''
	Find source files in a directory recursively. Return an array
	containing the full path to each of source files found.

	directory would be a string defining the directory to search
	through recursively
	sourceExtension is a string in the form of ".py" so some more
	examples would be ".sh",".js",".cpp",".css",".html"
	'''
	sourcesArray = []
	directoryItems = listdir(directory)
	# for each location (file or directory) in this directory
	for location in directoryItems:
		# get the absolute location
		location=realpath(pathJoin(directory,location))
		if isfile(location):
			# check if the file is a selected source type
			if '.' in location:
				if sourceExtension[1:] == location.split('.')[1]:
					# check if the ignore list has been set
					if ignoreList != None and len(ignoreList) != 0:
						for ignoreItem in ignoreList:
							# check if the file is in the ignore list
							if ignoreItem not in location:
								# this is a file, append it to the returned files
								sourcesArray.append(realpath(pathJoin(directory, location)))
					else:
						# this is a file, append it to the returned files
						sourcesArray.append(realpath(pathJoin(directory, location)))
		elif isdir(location):
			# this is a directory so go deeper
			sourcesArray += findSources(pathJoin(directory, location), sourceExtension, ignoreList)
	# this function is dumb and has no false return values
	return sourcesArray
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
		# create the directories that the report will be stored in
		runCmd("mkdir -p report")
		runCmd("mkdir -p report/webstats")
		runCmd("mkdir -p report/lint")
		runCmd("mkdir -p report/trace")
		# copy the logo into the report
		runCmd("cp -v logo.png report/logo.png")
		# begin running modules for project-report
		if runLint == True:
			self.pylint(projectDirectory)
		if runDocs == True:
			self.pydocs(projectDirectory)
		if len(self.traceFiles) > 0:
			self.trace(projectDirectory)
		if runGitLog == True:
			self.gitLog()
		if runGitStats == True:
			self.gitStats()
		if runGource == True:
			self.gource()
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
		if pathExists(pathJoin(projectDirectory,'report','webstats','index.html')):
			reportIndex += "<a class='menuButton' href='webstats/index.html'>Stats</a>\n"
		if pathExists(pathJoin(projectDirectory,'report','log.html')):
			reportIndex += "<a class='menuButton' href='log.html'>Log</a>\n"
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
			searchString = 'code has been rated at '
			tempQuality = tempQuality[tempQuality.find(searchString)+len(searchString):]
			tempQuality = tempQuality[:tempQuality.find('/')]
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
			reportIndex += "<a class='menuButton' style='float:right' href='trace/index.html'>trace</a>\n"
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
		traceIndex += runCmd('python -m cProfile -s ncalls '+pathJoin(projectDirectory,relpath(filePath)))
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
			runCmd('pycallgraph --max-depth '+str(self.maxTraceDepth)\
				+' graphviz --output-file='+pathJoin(relpath(projectDirectory),'report','trace',(fileName+'.png'))\
				+' '+pathJoin(projectDirectory,filePath))
			traceFile += "<hr />"
			traceFile += '<div><pre>'
			# generate the cprofile output for the trace file
			traceFile += runCmd('python -m cProfile -s ncalls '+pathJoin(projectDirectory,relpath(filePath)))
			traceFile += '</pre></div>'
			traceFile += '</body></html>'
			# write the traceFile
			saveFile(pathJoin(projectDirectory,'report/trace/',(fileName+'.html')), traceFile)
	#######################################################################
	def pylint(self,projectDirectory):
		'''
		Run pylint for each .py file found inside of the project directory.
		'''
		debug.add('starting pylint process')
		debug.add('obtaining list of source files')
		# get the real path of the project directory
		projectDirectory = realpath(projectDirectory)
		# get a list of all the python source files, this is to find the paths
		# of all python source files
		sourceFiles = findSources(projectDirectory, '.py', self.ignoreList)
		# generate the pylint index file
		lintIndex  = "<html><style>"
		lintIndex += "td{border-width:3px;border-style:solid;}"
		lintIndex += "th{border-width:3px;border-style:solid;"
		lintIndex += "color:white;background-color:black;}"
		lintIndex += "</style><body>"
		lintIndex += "<a href='../index.html'><h1 id='#index'>Main Project Report</h1></a><hr />"
		lintIndex += "<div style='float: right;'>"
		lintIndex += "<h1 id='#index'>Index</h1><hr />"
		for filePath in sourceFiles:
			# pull filename out of the filepath and generate a directory file link
			filePath=filePath.split('/').pop()
			filePath=filePath[:(len(filePath)-3)]
			# write the index link
			lintIndex += '<a href="'+filePath+'.html">'+filePath+'</a><br />'
		lintIndex += "<hr />"
		lintIndex += "</div>"
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
		saveFile(pathJoin(projectDirectory,'report/lint/index.html'), lintIndex)
		# generate the individual files
		for filePath in sourceFiles:
			# grab the filename by spliting the path and poping the last element
			fullFileName=filePath.split('/').pop()
			# remove .py from the fileName to make adding the html work
			fileName=fullFileName[:(len(fullFileName)-3)]
			debug.add('Generating pylint report for file',filePath)
			# run pylint on the code and generate related page
			lintFile  = "<html><style>"
			lintFile += "td{border-width:3px;border-style:solid;}"
			lintFile += "th{border-width:3px;border-style:solid;"
			lintFile += "color:white;background-color:black;}"
			lintFile += "</style><body>"
			# place the location of the file
			lintFile += "<h2>"+relpath(filePath)+"</h2><hr />"
			# create the index box
			lintFile += "<div style='float: right;'><a href='index.html'><h1 id='#index'>Index</h1></a><hr />"
			# build the index linking to all other lint files
			for indexFilePath in sourceFiles:
				# pull the filename without the extension out of the indexfilepath
				indexFileName=indexFilePath.split('/').pop()
				indexFileName=indexFileName[:(len(indexFileName)-3)]
				# building the link index
				lintFile += '<a href="'+indexFileName+'.html">'+indexFileName+'</a><br />'
			lintFile += "<hr />"
			lintFile += "</div>"
			# create the uml diagram
			runCmd('pyreverse '+relpath(filePath)+' -o '+fullFileName+'.dot')
			runCmd('dot -Tpng *.'+fullFileName+'.dot > report/lint/'+fileName+'.png')
			# remove uml file that was previously generated
			runCmd('rm *.'+fullFileName+'.dot')
			# build the content
			lintFile += '<img src='+fileName+'.png />'
			# adding pylint output for the file to the report
			lintFile += runCmd('pylint --include-naming-hint="y" -f html\
				--rcfile="/usr/share/project-report/configs/pylint.cfg" '+\
				filePath)
			lintFile += "<hr />"
			# write the lintFile
			saveFile(pathJoin(projectDirectory,'report/lint/',(fileName+'.html')), lintFile)
	#######################################################################
	def pydocs(self,directory):
		'''
		Run pydocs for each .py file in the project directory.
		'''
		debug.add('running pydocs section')
		# generate python documentation
		runCmd('mkdir -p report/docs/')
		# for all python files create documentation files
		sourceFiles = findSources(directory,'.py', self.ignoreList)
		for location in sourceFiles:
			debug.add('RUNNING DOCUMENTATION FOR')
			debug.add(location)
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
				runCmd("pydoc -w "+location)
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
		logOutput  = "<html>"
		if pathExists('/usr/share/project-report/configs/style.css'):
			logOutput += "<head><style>\n"
			logOutput += loadFile('/usr/share/project-report/configs/style.css')
			logOutput += "\n</style></head>\n"
		logOutput += "<body>"
		logOutput += "<h1><a href='index.html'>Back</a></h1>"
		# generate the log into a variable
		logOutput += "<hr /><code><pre>"
		logOutput += escapeHTML(runCmd("git log --stat")).replace('\ncommit','</pre></code><hr /><code><pre>commit')
		logOutput += "</pre></code>"
		logOutput += "</body>"
		logOutput += "</html>"
		saveFile('report/log.html', logOutput)
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

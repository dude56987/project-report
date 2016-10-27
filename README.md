Project Report
==============

Generate website reports for git repositories. 

- Generate pylint report on all python files
- Run pydoc to create python documentation for all python files
- Generate a webpage containing git logs and diffs for each commit
- Run gitstats to generate website of statistics about the project over time
- Generate gource video of project commits and changes over time

##Usage

To generate a project report from within the current working directory of a git repo. You would use the command.
	
	project-report

To generate a report for a specific directory.

	project-report /path/to/your/git/project/directory

A website will be generated in a /report/ directory. Made in the current working directory the command is ran from.

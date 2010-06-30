#Makefile: part of pycanlib, builds pycanlib's documentation.
#
#Copyright (C) 2010 Dynamic Controls
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#Contact details
#---------------
#
#Postal address:
#    Dynamic Controls
#    17 Print Place
#    Addington
#    Christchurch 8024
#    New Zealand
#
#E-mail: bpowell AT dynamiccontrols DOT com

RST_SOURCE_FILES = pycanlib_srs.txt pycanlib_manual.txt

all: pdf

RM = del /Q
RMDIR = rmdir /S /Q
#RM = rm -f
#RMDIR = rm -f

pdf: ${RST_SOURCE_FILES:.txt=.pdf}
tex: ${RST_SOURCE_FILES:.txt=.tex}

%.tex: %.txt
	@echo $(RST_SOURCE_FILES)
	@echo Converting $* to TeX...
	@python C:\Python26\Scripts\rst2latex.py $*.txt $@ --stylesheet=dcl_srs_stylesheet.sty
	@echo Done!

%.pdf: %.tex
	@echo Converting $* to PDF...
	@pdflatex --quiet $*.tex $@
	@pdflatex --quiet $*.tex $@
	@pdflatex --quiet $*.tex $@
	@echo Done!

clean:
	@echo Cleaning up temp files...
	-@$(RM) *.aux
	-@$(RM) *.out
	-@$(RM) *.log
	@echo Cleaning up output files...
	-@$(RM) *.pdf
	-@$(RM) *.tex
	@echo Done!

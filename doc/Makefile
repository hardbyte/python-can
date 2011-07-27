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

RST_SOURCE_FILES = pycanlib_srs.txt pycanlib_manual.txt virtual.txt

# Windows:
#RST2LATEX = python C:\Python26\Scripts\rst2latex.py
#RST2HTML = python C:\Python26\Scripts\rst2html.py
#RM = del /Q
#RMDIR = rmdir /S /Q

# GNU/Linux:
RST2LATEX = rst2latex
RST2HTML = rst2html
LATEX2PDF = xelatex
RM = rm -f
RMDIR = rm -f

all: pdf
pdf: ${RST_SOURCE_FILES:.txt=.pdf}
tex: ${RST_SOURCE_FILES:.txt=.tex}
html: ${RST_SOURCE_FILES:.txt=.html}

test: clean ${RST_SOURCE_FILES:.txt=.test}

%.tex: %.txt
	@echo Converting $* to TeX...
	@$(RST2LATEX) $*.txt $@ --stylesheet=stylesheet.sty
	@echo Done!

%.pdf: %.tex
	@echo Converting $* to PDF...
	$(LATEX2PDF) $*.tex $@
	$(LATEX2PDF) $*.tex $@
	$(LATEX2PDF) $*.tex $@
	@echo Done!

%.html: %.txt
	@echo Converting $* to HTML...
	@$(RST2HTML) $*.txt $@
	@echo Done!

clean:
	@echo Cleaning up temp files...
	-@$(RM) *.aux
	-@$(RM) *.out
	-@$(RM) *.log
	-@$(RM) *.toc
	@echo Cleaning up output files...
	-@$(RM) *.pdf
	-@$(RM) *.tex
	-@$(RM) *.test
	-@$(RM) *.html
	@echo Done!

%.test: %.txt
	@python -m doctest -v $*.txt
	@echo "tested OK" > $@

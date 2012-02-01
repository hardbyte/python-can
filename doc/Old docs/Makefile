#Makefile: part of pycanlib, builds pycanlib's documentation.

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

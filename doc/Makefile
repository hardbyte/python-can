RST_SOURCE_FILES = pycanlib_srs.txt

all: pdf

#RM = del /Q
#RMDIR = rmdir /S /Q
RM = rm -f
RMDIR = rm -f

pdf: ${RST_SOURCE_FILES:.txt=.pdf}
tex: ${RST_SOURCE_FILES:.txt=.tex}

%.tex: %.txt
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
	-@$(RM) *.aux *.out *.log
	@echo Cleaning up output files...
	-@$(RM) *.pdf *.tex
	@echo Done!

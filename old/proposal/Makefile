#
# $Id: Makefile.master,v 1.11 2007/09/20 18:15:50 lijun Exp $
#
# Master makefile for Latex2e-based documents.  I have finally
# integrated all of my different Makefiles into this master copy
# because I got tired of always trying to find out where my latest
# ideas lived.  To use this, symlink Makefile.master into a main
# directory and then type 
#        make -f Makefile.master BASE=basename update-Makefile
# Further edits should then be made between the "BEGIN
# EDIT SECTION nn" and "END EDIT SECTION nn" comments.  Changes made outside
# those areas count as improvements, which should be back-merged into
# netsec/netsec.latex/Makefile.master; usually, that can be done by editing
# the symlinked copy.  A repeat of "make update-Makefile" will
# regenerate the target Makefile, integrating any changes made
# (anywhere) to Makefile.master, but preserving site-specific material
# between the "BEGIN/END EDIT SECTION" comments.  Note that there are
# multiple edit sections; each is numbered individually and in
# ascending (but not consecutive) sequence.
#
# Bugs: if there are duplicate edit section numbers, the sections will
# be concatenated (including multiple occurrences of the begin/end
# comments).  The numbered edit sections are inserted into the new
# Makefile in order and in the places where they appear in the master.
# If the master Makefile contains out-of-order sections, edit sections
# from the previous Makefile will be duplicated.
#
# $Log: Makefile.master,v $
# Revision 1.11  2007/09/20 18:15:50  lijun
# "all" is "allpdf" instead of "allps"
#
# Revision 1.10  2007/03/16 05:53:18  tehrenkr
# make a review command
#     depends on $(BASE).pdf then scp it to your ~/public_html/ directory
#
# Revision 1.9  2005/06/15 07:51:24  lijun
# Several fixes of Jeremy was incorrect.  Fixed.
#
# Revision 1.8  2005/04/15 21:36:42  yozik
#
# updated to newer version per Jun Li`s request.
# Made minor changes to new version to reflect those that were made to local copy
#
# Revision 1.5  2005/04/08 22:27:29  geoff
# When generating dependencies, always trust an explicitly specified
# three-letter suffix over a generated one.
#
# Revision 1.4  2005/02/06 23:25:21  geoff
# Add 'update-makefile' as an alternate spelling.  Allow includegraphics
# calls to specify explicit extensions other than eps.
#
# Revision 1.3  2005/01/31 22:52:33  geoff
# Incorporate NSF`s recommended ps2pdf switches
#
# Revision 1.2  2005/01/13 16:46:50  geoff
# Move the RCS log to a better place.  Add support for passing arbitrary
# Latex commands to the head of the document, and use it to
# automatically pass the paper size.  Fix the commented-out .dvi.pdf
# rule to use a recursive invocation of the Latex loop.
#
# Revision 1.1  2005/01/07 13:19:13  geoff
# Initial revision
#
SHELL	=	/bin/sh
BIBTEX	=	bibtex
DVIPS	=	dvips
GIFTOPNM =	giftopnm
JGRAPH	=	jgraph
JPEG2PS	=	jpeg2ps
LATEX	=	latex
MAKEINDEX =	makeindex
PDFLATEX =	pdflatex
PNMTOPS =	pnmtops
PS2PDF	=	ps2pdf
#PSOPTIONS =	psoptions
RM	=	rm
TGIF	=	tgif
TTH	=	tth

# BEGIN EDIT SECTION 10

WEBLOC = "cs.uoregon.edu:~/public_html/"

# BASE is the BASE name of the TeX file to use.  Usually, this will be
# auto-generated.
BASE	=	main

# FIGURES is the list of files (usually figures) on which the main
# document depends.  Some figures are automatically detected using
# "make depend".  Anything not autodetected should be listed here.
FIGURES	=

# BUILTFIGURES is the list of files (usually figures) that are
# automatically created as part of building the main document.
# Everything in BUILTFIGURES is removed as part of "make clean"; if
# you don`t want something cleaned up, list it in FIGURES instead.
BUILTFIGURES =

# BIBS is the list of bibliography files on which the main document
# depends.  If a bibliography file lives in a different directory, a
# proper relative or absolute path should be given.
BIBS	=	#$(BASE).bib

# END EDIT SECTION 10

# BEGIN EDIT SECTION 20

# PAPERSIZE is the capitalized encoding of the chosen paper size.  A
# lowercase encoding is generated automatically when needed.  By
# default, PAPERSIZE is "Letter".  It can also be useful to set it to
# $(LC_PAPER).
#
# Warning: the PAPERSIZE given here has nothing to do with the paper
# size specified as a \documentclass option.  However, it is passed to
# the Latex document (in lowercase) in the "\papersize" variable, so
# you can include it in the document class with:
#	\documentclass[options,\papersize paper]{...}
PAPERSIZE =	Letter

# LATEXDEFS is a set of Latex commands that should precede the
# document itself.  It can be used to select document variations, etc.
# Usually, LATEXDEFS will be set to a default (often null) here and
# then overridden using a recursive invocation of make.
LATEXDEFS =

# Switch options.
# LATEXSW and DVIPSSW are self-explanatory.
LATEXSW	=
DVIPSSW	=	-t $(PAPERSIZE) -P cmz -e 0
# DVIPSPDFSW is switches passed to dvips when the result is intended
# to be converted to PDF.
DVIPSPDFSW =	-t $(PAPERSIZE) -P pdf -G0
# PDFLATEXSW
PDFLATEXSW =
# PNMTOPSSW is switches passed to pnmtops when converting images to
# figures.
PNMTOPSSW =	-noturn -equalpixels
#
# Use the first option below for NSF Fastlane
PS2PDFSW =	-dMaxSubsetPct=100 -dSubsetFonts=true -dEmbedAllFonts=true \
		-dCompatibilityLevel=1.2
#PS2PDFSW =
# PSOPTIONSSW is given to psoptions to select double-sided printing,
# stapling, etc.
PSOPTIONSSW =	canon duplex top-left
# TGIFSW is given to tgif when generating eps output files.
TGIFSW	=	 -print -eps -reqcolor
# TTHSED is a little SED script used to clean up tth output.
TTHSED	=	's/H3/H4/g;s/H2/H3/g;s/H1/H2/g;/File translated from/d'

# END EDIT SECTION 20

#
# The following list gives the suffixes of files that TeX may create
# as a side effect, and which may change as the result of multiple TeX
# runs.
#
AUXFILES =	aux bbl fot glo gtb idx ind lof los lot toc

.SUFFIXES:	.pdf .ps .dvi .html .tex .eps .gif .jpg .jgr .obj

# BEGIN EDIT SECTION 30

# The following targets don't usually need to be changed, but if the
# targets don't match the naming scheme (e.g., $(BASE)_master.dvi and
# $(BASE)_answers.dvi, as I use for exams) then they can be changed
# here.

all:	allpdf

alldvi:	$(BASE).dvi

$(BASE).dvi:	$(BASE).tex $(FIGURES) $(BUILTFIGURES) $(BIBS)

allps:	$(BASE).ps

allpdf:	$(BASE).pdf

allhtml:	$(BASE).html

alleps:
	@for i in *.jgr; do \
	    $(MAKE) `basename $$i .jgr`.eps; \
	done
	@for i in *.jpg; do \
	    $(MAKE) `basename $$i .jpg`.eps; \
	done

# Insert rules for specialized targets here.

# END EDIT SECTION 30

# Rules for compiling TeX files.  This is a very complicated rule
# because it supports all sorts of LaTeX options and can build many
# types of LaTeX auxiliary files (e.g., bibliographices, indices,
# tables of contents, etc.)
.tex.dvi:
	@set +e; \
	    pass=1; \
	    while [ $$pass -le 5 ]; \
	    do \
		echo === $(LATEX) Pass $$pass ===; \
		for suff in $(AUXFILES); \
		do \
		    [ -r $*.$$suff ]  &&  cp $*.$$suff $*.X$$suff; \
		done; \
		papersize=`echo "$(PAPERSIZE)" | tr '[A-Z]' '[a-z]'`; \
		$(LATEX) $(LATEXSW) \
		  "\batchmode \def\papersize{$$papersize} $(LATEXDEFS) \input $*"; \
		stat=$$?; \
		if [ $$stat -ne 0 ]; then break; fi; \
		ok=yes; \
		egrep -s bibdata $*.aux 2>/dev/null  &&  $(BIBTEX) $*; \
		if [ -r $*.idx ]; then \
		    $(MAKEINDEX) $*; \
		fi; \
		for suff in $(AUXFILES); \
		do \
		    if [ -r $*.$$suff ]; \
		    then \
			if cmp -s $*.$$suff $*.X$$suff; \
			then \
			    : ; \
			else \
			    ok=no; \
			    break; \
			fi; \
		    fi; \
		done; \
		rm -f $*.X*; \
		if [ $$ok = yes ]; \
		then \
		    break; \
		fi; \
		pass=`expr $$pass + 1`; \
	    done; \
	    echo === $(LATEX) Log ===; \
	    cat $*.log; \
	    [ -r $*.blg ]  &&  cat $*.blg; \
	    if [ $$stat -ne 0 ]; then exit $$stat; else echo foo >/dev/null; fi

.dvi.ps:
	$(DVIPS) $(DVIPSSW) -f < $*.dvi > $*.ps
#	$(DVIPS) $(DVIPSSW) -f < $*.dvi | $(PSOPTIONS) $(PSOPTIONSSW) > $*.ps

.dvi.pdf:
	$(DVIPS) $(DVIPSPDFSW) -f < $*.dvi | $(PS2PDF) $(PS2PDFSW) - $*.pdf

# The .ps.pdf rule is disabled so that we can be sure to use the
# .dvi.pdf rule above, which invokes divps with somewhat different
# switches to achieve better results.
#
#.ps.pdf:
#	$(PS2PDF) $(PS2PDFSW) $*.ps

# Note that this rule pretends to make the dvi file so that it can
# invoke the complex Latex loop above.
#
# This rule is disabled (see alternate rule above) because pdflatex
# doesn`t handle EPS files.
#
#.tex.pdf:
#	$(MAKE) LATEX=$(PDFLATEX) "LATEXSW=$(PDFLATEXSW)" $*.dvi

# We make the dvi file to make sure tth has the proper auxiliary files.
.tex.html:
	$(MAKE) $*.dvi
	$(TTH) -L$* < $*.tex | sed $(TTHSED) > $*.html

.jgr.eps:
	$(JGRAPH) "$<" > "$@"

.obj.eps:
	$(TGIF) $(TGIFSW) "$<"

.jpg.eps:
	$(JPEG2PS) -p `echo "$(PAPERSIZE)" | tr '[A-Z]' '[a-z]'` "$<" > "$@"

.gif.eps:
	$(GIFTOPNM) "$<" | $(PNMTOPS) $(PNMTOPSSW) > "$@"

# BEGIN EDIT SECTION 90

# Insert specialized .x.y rules here.  Usually, though, those should
# go in Makefile.master, not here.

review: $(BASE).pdf
	scp $(BASE).pdf $(WEBLOC)

# END EDIT SECTION 90

#
# Rules for building the Makefile itself.  See comments at the top.
# Requires GNU or (maybe) Posix awk; untested with the latter.
#
# This rule is written so that "make update-Makefile" will ALWAYS
# update the Makefile.  For that reason, the target isn`t named just
# "Makefile"; in this fashion, you can make other targets depend on
# the Makefile itself.
#
update-makefile update-Makefile:	FRC
	[ -r Makefile ]  ||  cp Makefile.master Makefile
	if [ -z "$(BASE)" ]; then \
	    base=`ls *.tex | sed 's/.tex$$//;1q'`; \
	else \
	    base="$(BASE)"; \
	fi; \
	awk 'BEGIN { base = "'"$$base"'"; section = 0; lastSection = 0 } \
	    FILENAME=="Makefile" \
	      { if ($$0 ~ /^# BEGIN EDIT SECTION/) section = $$5 + 0; \
		if (section != 0) \
		  { if (lines[section] != "") \
		      lines[section] = lines[section] "\n"; \
		    if ($$0 ~ /^BASE[ 	]=/) \
		      $$0 = "BASE	=	" base; \
		    lines[section] = lines[section] $$0; \
		  } \
		if ($$0 ~ /^# END EDIT SECTION/) section = 0; \
		next; \
	      } \
	      { if ($$0 ~ /^# BEGIN EDIT SECTION/) \
		  { for (i = lastSection + 1; i < $$5 + 0; i++) \
		      if (lines[i] != "") print lines[i]; \
		    section = lastSection = $$5 + 0; \
		  } \
		if (section == 0) print; \
		if ($$0 ~ /^# END EDIT SECTION/) \
		  { section = 0; \
		    print lines[lastSection]; \
		  } \
	      }' \
	  Makefile Makefile.master > Makefile.new
	mv Makefile Makefile.bak2
	mv Makefile.new Makefile
	$(MAKE) depend
	mv Makefile.bak2 Makefile.bak

FRC:

#
# Create dependencies.  Bug: assumes at most one \include or similar
# command per line.
#
depend:
	rm -f Makefile.bak
	mv Makefile Makefile.bak
	sed '/^# DO NOT DELETE THIS LINE/,$$d' Makefile.bak > Makefile
	echo '# DO NOT DELETE THIS LINE' >> Makefile
	echo '#' >> Makefile
	echo '# Automatically generated dependencies follow.' >> Makefile
	echo '#' >> Makefile
	grep '\\' *.tex \
	  | sed -n -e 's/^\([^:]*\)\.tex:.*\\codesample{\(.*\)}.*$$/\1.dvi: \2/p' \
	    -e 's/^\([^:]*\)\.tex:.*\\input{\(.*\)}.*$$/\1.dvi: \2.tex/p' \
	    -e 's/^\([^:]*\)\.tex:.*\\input \([^ ]*\)$$/\1.dvi: \2.tex/p' \
	    -e 's/^\([^:]*\)\.tex:.*\\include{\(.*\)}.*$$/\1.dvi: \2.tex/p' \
	    -e 's/^\([^:]*\)\.tex:.*\\epsffile{\(.*\)}.*$$/\1.dvi: \2.eps/p' \
	    -e 's/^\([^:]*\)\.tex:.*\\epsffig{.*file=\([^,]*\).*}.*$$/\1.dvi: \2.eps/p' \
	    -e 's/^\([^:]*\)\.tex:.*\\includegraphics[^{]*{\(.*\)\.\(.*\)}.*$$/\1.dvi: \2.\3/p' \
	    -e 's/^\([^:]*\)\.tex:.*\\includegraphics[^{]*{\(.*\)}.*$$/\1.dvi: \2.eps/p' \
	  | sed -e 's/\(\.[a-z][a-z][a-z]\)\.[a-z][a-z][a-z]$$/\1/' \
	  >> Makefile

clean:
	$(RM) -f *.ilg *.log *.dvi *.blg *.X??? *.out *.ps $(BASE).pdf
	$(RM) -f `echo $(AUXFILES) | sed 's/^/*./;s/ / *./g'`
	$(RM) -f $(BUILTFIGURES) Makefile.bak Makefile.bak2

#
# DO NOT DELETE THIS LINE
#
# Automatically generated dependencies follow.
#

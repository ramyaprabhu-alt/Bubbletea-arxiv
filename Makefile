TEXS=$(wildcard *.tex */*.tex)
PAPER=main
LATEXMK=latexmk -pdf -interaction=nonstopmode -halt-on-error -shell-escape

all:	$(PAPER).pdf

$(PAPER).pdf:   $(TEXS) main.bib $(PAPER).glo
	$(LATEXMK) $(PAPER).tex

$(PAPER).glo:
	touch $@ 

figs:
	$(MAKE) -f $(PAPER).makefile -j

fig:
	rm -f figures/$(FIG).pdf && $(MAKE) figs || { if [ -t 1 ]; then vim figures/$(FIG).log +$$; else tail -40 figures/$(FIG).log; exit 1; fi; }

figwidth:
	bash meta/figwidth.sh $(FIG) $(TARGET)

down:																		
	git stash && git pull && git stash pop
 
up:																			
	git stash && git pull && git push && git stash pop

clean:
	$(LATEXMK) -C $(PAPER).tex
	rm -f $(PAPER).out $(PAPER).bbl $(PAPER).auxlock

.PHONY: all clean figs fig figwidth down up

#!/bin/bash
# Fit an externalized grouped plot to the line width: rebuild it, measure
# its PDF, correct `width=<W>pt` by gap/columns, repeat until within TOL.
# Usage: meta/figwidth.sh <plot name> [target width in pt]
set -e
export LC_ALL=C  # awk: dot decimals under a French locale
fig=$1
src=plots/$fig.tex
tol=0.2
[ -f "$src" ] || { echo "no $src"; exit 1; }

# panels per row from `group size=<cols> by <rows>`, 1 for a single axis
cols=$(grep -oE 'group size=[0-9]+' "$src" | head -1 | grep -oE '[0-9]+$' || true)
cols=${cols:-1}

# target: \textwidth in figure*, \columnwidth in figure or in a
# \columnwidth minipage (mlsys2025.sty); other boxes need it passed
if [ -n "$2" ]; then
  target=$2
else
  env=$(awk -v f="\\\\inputplot\\{$fig\\}" '
    FNR==1 {e=""; m=""}
    /^[ \t]*%/ {next}
    /\\begin\{figure\*\}/ {e="figure*"} /\\begin\{figure\}/ {e="figure"}
    /\\begin\{minipage\}/ {m=$0; sub(/.*\\begin\{minipage\}(\[[^]]*\])*\{/, "", m); sub(/\}.*/, "", m)}
    /\\end\{minipage\}/ {m=""}
    $0 ~ f {if (/\\resizebox/) print "resized"; else if (m != "") print "minipage:" m; else print e; exit}' sections/*.tex)
  case $env in
    figure\*) target=487.8225 ;;
    figure|minipage:\\columnwidth) target=234.87688 ;;
    resized) echo "$fig is scaled by \\resizebox; its width option does not matter"; exit 0 ;;
    minipage:*) echo "$fig is in a ${env#minipage:} minipage; pass TARGET=<pt>"; exit 1 ;;
    *) echo "\\inputplot{$fig} not found in a figure; pass TARGET=<pt>"; exit 1 ;;
  esac
fi

# `width=<W>pt` options (not `bar width`), one value shared by all groups
widths() { perl -nle 'print $1 while /(?:^\s*|,\s*)width=([0-9.]+)pt/g' "$src"; }
n=$(widths | sort -u | wc -l | tr -d ' ')
[ "$n" = 1 ] || { echo "$src: need one 'width=<W>pt' value, found $n:" $(widths); exit 1; }

for i in 1 2 3 4; do
  rm -f "figures/$fig.pdf"
  make -s -f main.makefile "figures/$fig.pdf" >/dev/null ||
    { tail -40 "figures/$fig.log"; exit 1; }
  # pdfinfo reports bp; TeX lengths are pt
  wd=$(pdfinfo "figures/$fig.pdf" | awk '/Page size/ {printf "%.3f", $3*72.27/72}')
  w=$(widths | head -1)
  gap=$(awk -v t="$target" -v x="$wd" 'BEGIN {printf "%.3f", t-x}')
  if awk -v g="$gap" -v t="$tol" 'BEGIN {exit !(g<t && g>-t)}'; then
    echo "$fig: width=${w}pt gives a ${wd}pt figure for a ${target}pt line, gap ${gap}pt: OK"
    exit 0
  fi
  echo "$fig: width=${w}pt gives a ${wd}pt figure for a ${target}pt line, gap ${gap}pt: adjusting"
  new=$(awk -v w="$w" -v g="$gap" -v c="$cols" 'BEGIN {printf "%.2f", w+g/c}')
  perl -pi -e "s/(^\\s*|,\\s*)width=\\Q$w\\Ept/\${1}width=${new}pt/g" "$src"
done
echo "did not converge; last width=${new}pt"
exit 1

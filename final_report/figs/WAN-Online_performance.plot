reset
set term postscript eps color enhanced "Helvetica" 25
set ylabel "Latency (min)"
set xlabel "File Size (MB)"
set output "WAN-Online_performance.eps"
set title "Total Sync Time by File and Group Size (WAN)" 
set logscale x 2
set key top left
plot "wandata8" using 1:($2/60) title "8 clients" with lines lw 3, \
"wandata4" using 1:($2/60) title "4 clients" with lines lw 3, \
"wandata2" using 1:($2/60) title "2 clients" with lines lw 3

reset
set term postscript eps color enhanced "Helvetica" 25
set ylabel "Latency (min)"
set xlabel "File Size (MB)"
set output "Dropbox_Performance.eps"
set title "Time to Sync Files: Dropbox Vs. D-Sync"
set logscale x 2
set key top left
plot "drop_data" using 1:($2/60) title 'Dropbox' with lines lw 3, \
"dsync-data" using 1:($2/60) title 'D-Sync' with lines lw 3

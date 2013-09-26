reset
set term postscript eps color enhanced "Helvetica" 25
set ylabel "Latency (min)"
set xlabel "File Size (MB)"
set xrange[1:256]
set yrange[0:18]
set output "LAN-Online_performance.eps"
set title "Total Sync Time by File and Group Size (LAN)"
set key top left
set logscale x 2
plot "data3" using 1:($2/60) title "8 clients" with lines lw 3, \
"data2" using 1:($2/60) title "4 clients" with lines lw 3, \
"data1" using 1:($2/60) title "2 clients" with lines lw 3

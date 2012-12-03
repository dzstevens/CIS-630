reset
set term postscript eps color enhanced "Helvetica" 25
set ylabel "Latency (min)"
set xlabel "File Size (MB)"
set xrange[1:1024]
set output "LAN-Online_performance.eps"
set title "Time to Sync Files with Group by File and Group Size"
set key top left
plot "data3" using 1:($2/60) title "8 clients" with lines lw 3, \
"data2" using 1:($2/60) title "4 clients" with lines lw 3, \
"data1" using 1:($2/60) title "2 clients" with lines lw 3

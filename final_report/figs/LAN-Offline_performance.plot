reset
set term postscript eps color enhanced "Helvetica" 25
set ylabel "Latency (min)"
set xlabel "File Size (MB)"
set output "LAN-Offline_Performance.eps"
set title "Time to Sync Files with New User by File and Group Size" 
set key top left
plot "offlinedata3" using 1:($2/60) title "8 clients" with lines lw 3, \
"offlinedata2" using 1:($2/60) title "4 clients" with lines lw 3, \
"offlinedata1" using 1:($2/60) title "2 clients" with lines lw 3

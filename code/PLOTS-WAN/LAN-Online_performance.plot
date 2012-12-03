reset
set term postscript eps color enhanced "Helvetica" 25
set ylabel "Latency (s)"
set xlabel "File Size (MB)"
set output "LAN-Online_performance.eps"
set title "LAN - Online Performance"
plot "data1" using 1:2 title "2 clients" with lines lw 3, \
"data2" using 1:2 title "4 clients" with lines lw 3, \
"data3" using 1:2 title "8 clients" with lines lw 3
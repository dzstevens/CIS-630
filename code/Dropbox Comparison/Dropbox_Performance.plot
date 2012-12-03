reset
set term postscript eps color enhanced "Helvetica" 25
set ylabel "Latency (min)"
set xlabel "File Size (MB)"
set output "Dropbox_Performance.eps"
set title "Sync Time For 2 Clients: Dropbox Vs. D-Sync"
set logscale x 2
set key top left
plot "drop_data_wan" using 1:($2/60) title 'Dropbox (WAN)' with lines lw 3, \
"dsync_data_wan" using 1:($2/60) title 'D-Sync (WAN)' with lines lw 3, \
"dsync_data_lan" using 1:($2/60) title 'D-Sync (LAN)' with lines lw 3

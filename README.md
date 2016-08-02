# TopCurse

A small system monitoring utility with line graphs of CPU performance and various other statistics (packets over Ethernet and WiFI, disk transfers, memory paging & swapping, etc) implemented in `python` with `ncurses`

### Why?
Because it's midnight at a hackathon and why not?

### Line graphs?
Yep! Note that the graphs show only relative CPU usage among the top 10 processes in each time slice, not absolute usage

### Limitations
`TopCurse` makes no attempt to handle window size changes and assumes at least the standard `80x24` to work with

`TopCurse` is built against `Mac OS X 10.9`'s various system monitoring utilities and so may not be compatible with the equivalent utilities on your system
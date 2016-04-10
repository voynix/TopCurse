# TopCurse

A mini-`top` with line graphs of CPU performance implemented in `python` with `ncurses`

### Why?
Because it's midnight at a hackathon and why not?

### Line graphs?
Yep! Note that the graphs show only relative CPU usage among the top 10 processes in each time slice, not absolute usage

### Limitations
`TopCurse` makes no attempt to handle window size changes and assumes at least the standard `80x24` to work with
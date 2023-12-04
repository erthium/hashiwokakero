# Hashiwokakero Puzzle

Generator and solver algorithm repertoire for the Japanese logic puzzle Hashiwokakero created by Nikoli.

## Puzzle

Simplyfied rules from [Wikipedia](https://en.wikipedia.org/wiki/Hashiwokakero).

Played in rectangular grid. Encircled cells are islands numbers from 1 to 8 inclusive. The rest of the cells are empty.

The goal is to connect all of the islands by drawing a series of bridges between the islands. 

The bridges must follow certain criteria:
- All islands must be connected.
- Bridged cannot cross.
- Bridges are only established orthogonally, never diagonally.
- At most two bridges connect a pair of islands.
- An island must hold bridges that mathces it's own number.

Plot-twist is that there may not be only 1 solution. Sometimes the structure of the board allows to have 2 different ways to go and still fulfill all the rules.

## General Structure

Node: A class that holds basic values for board cells

class Node
    int type = 0->empty, 1->island, 2->bridge
    int bridge_count -> 1, 2 (only if type=2)

Board: A 2 dimensional array for Nodes


## Generator Algorithm

...will be worked on soon


## Solver Algorithm

Function that takes 2 dimensional array of Nodes as an input and returns the array filling the gaps, or -1 if it's unsolvable



Algorithm in psuedocode



func solve_hashi(board)
    Node[] islands = every Node in board that has type=1
    ...will be worked on soon


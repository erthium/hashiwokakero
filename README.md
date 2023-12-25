# Hashiwokakero Puzzle

Generator and solver algorithm repertoire for the Japanese logic puzzle Hashiwokakero - aka Hashi - created by Nikoli.

The project is still being worked on, check [issues](https://github.com/ErtyumPX/hashiwokakero/issues) and [milestones](https://github.com/ErtyumPX/hashiwokakero/milestones) for the process.

## License

This project is licensed under the [GNU GPL-3.0](https://github.com/ErtyumPX/hashiwokakero/blob/main/LICENSE) license.

## Setup

The project is written in Python 3.11.6, although should work on any Python Interpreten above 3.5.x.

Apart from built-in packages, only third party package is PyGame 2.4.0 with SDL 2.28.5.

Easy and mass puzzle generation scrips are currently being worked on, see [ISSUE#3](https://github.com/ErtyumPX/hashiwokakero/issues/3).

You can easily clone or fork the project, see below to find how to use source scripts.

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

<img src="https://github.com/ErtyumPX/hashiwokakero/assets/49292808/d4093342-5ae5-43e2-8fda-da4ad8901cec" width="250" height="250" title="Unsolved Hashi">
<img src="https://github.com/ErtyumPX/hashiwokakero/assets/49292808/3e6096df-abb5-4f02-a41e-70d7056f9337" width="250" height="250 title="Solved Hashi">

## General Structure

### Terminology

Full Grid: A grid that satisfies given w and h dimensions and has no empty edges.

Cycle Step: Iteration count of the generator algorithm. Since generation is random, 
it may not reach that iteration count. Still is important if the user wants to stop 
generating at some point

Max Puzzle: A puzzle which cannot be extended anymore, which has no node that could 
potentially have another bridge in an empty direction.

### Generator Algorithm

Will be written soon...

### Solver Algorithm

Will be written soon...


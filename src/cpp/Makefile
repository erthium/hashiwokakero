all: generator solver

generator: generator.cpp
	g++ generator.cpp -o bin/generator

solver: solver.cpp
	g++ solver.cpp -o bin/solver

rungen: bin/generator
	./bin/generator

runsol: solver
	./bin/solver

clean:
	rm -f ./bin/*
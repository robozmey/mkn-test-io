all:
	dune build

install:
	sudo apt-get install -y opam
	opam init
	opam switch -y create ./ --deps-only --with-test ocaml-base-compiler.4.12.0
	opam install -y dune.2.9.0

clean:
	dune clean || true

.PHONY: all install clean

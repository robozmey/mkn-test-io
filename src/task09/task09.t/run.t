Write your solution here
  $ alias CREATE='...'

  $ alias LINKS='...'

  $ alias REMOVE='...'

Tests
  $ CREATE

  $ LINKS

  $ cat file.txt
  Hello World!

  $ REMOVE

  $ cat soft
  cat: soft: No such file or directory
  [1]

  $ cat hard
  Hello World!

  $ CREATE

  $ cat soft
  Hello World!

  $ cat hard
  Hello World!

Write your solution here
  $ alias SOLUTION='...'

Tests
  $ ls A
  a.txt
  subA

  $ ls B
  dir

  $ ls A/subA
  a.txt
  b.txt
  subsubA

  $ SOLUTION

  $ ls A
  dir

  $ ls B
  a.txt
  subA

  $ ls B/subA
  a.txt
  b.txt
  subsubA

Write your solution here
  $ alias SOLUTION='ls $DIR/*.cpp | wc -l'

Tests
  $ DIR='dir' && (SOLUTION)
  3

  $ DIR='dor' && (SOLUTION)
  1

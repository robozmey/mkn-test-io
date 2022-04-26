Write your solution here
  $ alias SOLUTION='...'

Tests
  $ DIR='dir' && SOLUTION

  $ ls $DIR
  ls: cannot access 'dir': No such file or directory
  [2]

  $ DIR='empty' && SOLUTION

  $ ls $DIR
  ls: cannot access 'empty': No such file or directory
  [2]

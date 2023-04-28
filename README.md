 # Notes

 Throught day we are interacting with flow of information. It takes time to strucutre and organize it.

 Instead, this project dealls with 'atoms' of informaion, such as a web address, a command, a quick scribble. This is only intended by consumption by the author.

 It is ok if some of the notes lose meaning, - at least they did not take time.

 # Installing

Create script `f`:
 
  pipenv run python fcore.py script | source


Then define `=` function:

  cp equals.fish ~/.config/fish/conf.d/
 

 # Usage

All starts with `=`.

Just enter search terms, either interactively or from command line directly - it can be edited immediately after.

Modifiers:
  `.` - Only output one entry per `space`
  `@` - Only output entries from current `space`


Actions:
 `S` - `cd` to space
 `O` - `open` the note; only shows notes where it is meaningful
 `C` - copy to clipboard



 # Notes

 Throught day we are interacting with flow of information. It takes time to strucutre and organize it.

 Instead, this project deals with 'atoms' of informaion, such as a web address, a command, a quick scribble. This is only intended by consumption by the author.

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
  `@<kw>` - Output entries from spaces with `<kw>` in name


Actions:
 `S` - `cd` to space; if there is none, new will be created
 `O` - `open` the note; only shows notes where it is meaningful
 `C` - copy to clipboard


 # `f` command

 - `search <query>`: perform search aming notes, with the commands listed above.
 - `an <note text>`: add note.
 - `norm <file name>`: rename file so that it could be used in a note - without spaces.
 - `png <list of words>`: saves png and copies name to clipboard for use.
 - `last`: prints out minutes since last note for updated use; --all adds minor additional info. .tmux status 

 # TODO
- search inside txt 
- how exactly it is going to be set up
- snippets

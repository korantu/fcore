# Notes to Find

Notes tell me: 
 - What I wanted to do.
 - How I wanted to do it.
 - What I neededed to do it.

 Flow is ssuper important - and information has to be back in millisecondss.

 # Finding Core

 make all centralized

 # Installing

Create script `f`:
 
  
  pipenv run python fcore.py script | source

   pipenv run python fcore.py alias > ~/.config/fish/conf.d/fcore.fish # other shells should be working similarly
 

 # Usage

     `fp` - Find Project - looks in all notes and project names to zoom into the needed one. Then cd's there.
     `fn` - Find Note - looks through all notes and copies the selected one to the clipboard.
     `fo` - Find and Open - shows openable notes and opens them.
     `an` - Add Note - add note.

  When searching, `@` means from current project.

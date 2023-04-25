function =; 
	set search_string (if test -n "$argv"; echo $argv; else; echo '-'; end)
	set -x FZF_DEFAULT_COMMAND "f search $search_string"
        fzf --disabled --query="$search_string" --bind="change:reload(eval f search {q})"
end

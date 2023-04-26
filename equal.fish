function =; 
	set -x FZF_DEFAULT_COMMAND "f search \"$argv\""
        echo Running [(fzf --disabled --query="$argv" --bind="change:reload(eval f search {q})")]
end

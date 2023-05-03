function =; 
        set -x WAS (pwd)
	set -x FZF_DEFAULT_COMMAND "f search \"$argv\""
        echo ( fzf --disabled --query="$argv " --bind="change:reload(eval f search \"{q}\")" ) | source
end

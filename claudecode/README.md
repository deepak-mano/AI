library : AI\claudecode

crea_tb.md: (path :AI\claudecode\.claude\commands)
	Updates the database schema file stored test_db

Claude hooks:
Settings.Json -> used for connecting to models using litellm and hooks to trigger after the crea_tb.md inbuilt command
1) Trigger inspect_hook.py will parse to identify if a DB struture is updated
2) if updated, takes a backup of relation design doc and updates it with recent details

config.yaml: Litellm config to connect to nvdia nim models and to perform appropriate translation for anthropic to openAI format

drop_extension.py: to drop unwanted parameters from anthropic format before connecting to nvidia nim models




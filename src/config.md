### External editor Configuration

**editor** [string]: The text editor to use, some common values are:

- **vim -gf** ideal for old-school users
- **open -t** leaves MacOS make the decision
- **code** common handler for [VSCode](https://code.visualstudio.com/Download)
- **atom** for lightweight editor [atom](https://atom.io/)
- **notepad++.exe** Windows' popular [Notepad++](https://notepad-plus-plus.org/downloads/)

If the specified editor could not be found, it'll try to make an educated guess.

In Windows remember to escape backslashes, write them twice:

```
{
    "editor": "C:\\Windows\\sol.exe"
}
```


### Sending selected text to the external text editor

When you selected some text and press one of the shortcuts you've set the selected text will be put
into a temporary file and opened in the text editor. The file extension used for this temporary file
can bet set in two ways: You can use a field from your note with the config key
`file extension from field`. If this is not in the note or empty this add-on looks at your tags
according to the config key `tags to file ending`.

If you don't want to use a temporary file but instead always use the same file for selected contents
you can use `custom_files_for_langs` and set a file per language. This is a dictionary and you would
e.g. use `"py": "/home/user/Documents/the_one_file.py"`.

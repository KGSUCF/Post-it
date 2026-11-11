Set fso = CreateObject("Scripting.FileSystemObject")
Set wsh = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
wsh.Run "python """ & dir & "\postit.py""", 0, False

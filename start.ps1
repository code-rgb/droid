function CmdExists($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

if (CmdExists -cmdname 'poetry') {
    Write-Output "Checking Requirements..."
    poetry install | Out-Null
    poetry run python -m droid
}
else {
    python -m droid
}
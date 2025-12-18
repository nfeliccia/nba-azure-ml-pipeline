$localFile = Join-Path $PSScriptRoot "test_upload.txt"
"hello" | Set-Content $localFile
azcopy copy $localFile "https://stnba86412597.blob.core.windows.net/nba-raw/test_upload.txt"

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$recordingDir = Join-Path (Split-Path $PSScriptRoot -Parent) 'runtime/recording'
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 1
try {
    0..7 | ForEach-Object {
        $synth.SetOutputToWaveFile((Join-Path $recordingDir "narration_$_.wav"))
        $synth.Speak([System.IO.File]::ReadAllText((Join-Path $recordingDir "narration_$_.txt")))
    }
} finally { $synth.Dispose() }

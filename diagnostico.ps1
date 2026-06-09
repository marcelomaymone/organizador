$p = New-Object System.Diagnostics.Process
$p.StartInfo.FileName = "git.exe"
$p.StartInfo.Arguments = "--version"
$p.StartInfo.RedirectStandardOutput = $true
$p.StartInfo.RedirectStandardError = $true
$p.StartInfo.UseShellExecute = $false
try {
    $started = $p.Start()
    echo "Started: $started"
    if ($started) {
        $p.WaitForExit()
        echo "ExitCode: $($p.ExitCode)"
        echo "OUT: $($p.StandardOutput.ReadToEnd())"
        echo "ERR: $($p.StandardError.ReadToEnd())"
    } else {
        echo "Process did not start."
    }
} catch {
    echo "Exception details: $_"
    echo "Exception type: $($_.Exception.GetType().FullName)"
}

Add-Type -AssemblyName System.Device
$w = New-Object System.Device.Location.GeoCoordinateWatcher
$w.TryStart($false, [TimeSpan]::FromMilliseconds(8000)) | Out-Null
Start-Sleep -Seconds 4
$p = $w.Position.Location
if ($p.IsUnknown) {
    Write-Output "UNKNOWN"
} else {
    Write-Output ("{0},{1},{2}" -f $p.Latitude, $p.Longitude, $p.HorizontalAccuracy)
}

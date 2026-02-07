param(
  [string]$DateAM = "2025-10-15T10:30:00Z",
  [string]$DatePM = "2025-10-15T21:00:00Z",
  [string]$Season = "fall"
)

$ErrorActionPreference = "Stop"

$poly = @(
  @{name='NW'; lat=43.31925; lon=-73.23064},
  @{name='NE'; lat=43.32165; lon=-73.20444},
  @{name='SE'; lat=43.29906; lon=-73.21121},
  @{name='SW'; lat=43.30036; lon=-73.24005}
)

$centerLat = ($poly | Measure-Object -Property lat -Average).Average
$centerLon = ($poly | Measure-Object -Property lon -Average).Average

$points = @(
  @{name='CENTER'; lat=$centerLat; lon=$centerLon},
  @{name='MID_N'; lat=(($poly[0].lat+$poly[1].lat)/2); lon=(($poly[0].lon+$poly[1].lon)/2)},
  @{name='MID_E'; lat=(($poly[1].lat+$poly[2].lat)/2); lon=(($poly[1].lon+$poly[2].lon)/2)},
  @{name='MID_S'; lat=(($poly[2].lat+$poly[3].lat)/2); lon=(($poly[2].lon+$poly[3].lon)/2)},
  @{name='MID_W'; lat=(($poly[3].lat+$poly[0].lat)/2); lon=(($poly[3].lon+$poly[0].lon)/2)}
)

$times = @(
  @{label='AM'; dt=$DateAM},
  @{label='PM'; dt=$DatePM}
)

function Invoke-Predict {
  param(
    [double]$Lat,
    [double]$Lon,
    [string]$DateTime,
    [string]$HuntPeriod,
    [string]$Season
  )

  $body = @{
    lat = $Lat
    lon = $Lon
    date_time = $DateTime
    season = $Season
    fast_mode = $false
    hunt_period = $HuntPeriod
    include_camera_placement = $false
  } | ConvertTo-Json

  return Invoke-RestMethod -Method Post -Uri "http://localhost:8000/predict" -ContentType "application/json" -Body $body
}

$results = @()
foreach ($t in $times) {
  foreach ($p in $points) {
    $resp = Invoke-Predict -Lat $p.lat -Lon $p.lon -DateTime $t.dt -HuntPeriod $t.label -Season $Season

    $stands = @($resp.data.optimized_points.stand_sites)
    $best = $stands | Sort-Object -Property score -Descending | Select-Object -First 1

    $results += [pscustomobject]@{
      time = $t.label
      point = $p.name
      query_lat = [math]::Round([double]$p.lat, 6)
      query_lon = [math]::Round([double]$p.lon, 6)
      best_strategy = $best.strategy
      best_score = [math]::Round([double]$best.score, 3)
      best_lat = [math]::Round([double]$best.lat, 6)
      best_lon = [math]::Round([double]$best.lon, 6)
      bedding_n = @($resp.data.bedding_zones.features).Count
      feeding_n = @($resp.data.feeding_areas.features).Count
      effective_wind = $resp.data.wind_summary.overall_wind_conditions.effective_wind
      wind_conf = $resp.data.wind_summary.confidence_assessment
    }
  }
}

"\n=== Best stand per sample point (AM/PM) ===" | Write-Output
$results | Sort-Object time, point | Format-Table -AutoSize

"\n=== Strategy frequency ===" | Write-Output
$results | Group-Object best_strategy | Sort-Object Count -Descending | Select-Object Count, Name | Format-Table -AutoSize

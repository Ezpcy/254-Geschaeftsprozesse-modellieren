$engineEndpoint = "http://localhost:8080/engine-rest"
$UrlGetList = "$engineEndpoint/process-instance?active=false&suspended=false&withIncident=false&withoutTenantId=false&processDefinitionWithoutTenantId=false&rootProcessInstances=false&leafProcessInstances=false&variableNamesIgnoreCase=false&variableValuesIgnoreCase=false"
$UrlDeleteProcess = "$engineEndpoint/process-instance/{0}?skipCustomListeners=true&skipIoMappings=true&skipSubprocesses=false&failIfNotExists=false"

# Liste der vorhandenen Prozessinstanzen anfordern
$result = Invoke-WebRequest -Uri $UrlGetList -Method Get
$procInstances = $result | ConvertFrom-Json

# alle gefundenen Prozessinstanzen löschen
foreach ($procInstance in $procInstances)
{
  $UrlDeleteInstance = $UrlDeleteProcess -f $procInstance.id
  Write-Host ("Gelöscht wird Prozess {0}" -f $procInstance.id) -ForegroundColor Yellow

  $resDelete = Invoke-WebRequest -uri $UrlDeleteInstance -Method Delete

  if ($resDelete.StatusCode -lt 299)
  {
    Write-Host -ForegroundColor Green "Prozess erfolgreich gelöscht mit Resultat " $resDelete.StatusCode $resDelete.StatusDescription
  } else
  {
    Write-Host -BackgroundColor Red "Löschung ergab Fehler: " $resDelete.StatusCode $resDelete.StatusDescription
  }
}

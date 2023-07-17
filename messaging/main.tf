resource "aws_sns_platform_application" "apple-device" {
  name = var.sns_app_name
  platform = "APNS"
  platform_credential      = "MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgrvaVYqCWLrWQ6H/gCG8viuwYDk1DwKdbpIzzAAtb+U2gCgYIKoZIzj0DAQehRANCAARN1T1MdkMvNtxx8cLYuhSz+hLKkFJLOVvAy/hak1Pt3FWBxZHAh86g7mqDsxWWcnNyq/h8FrKzpMEdTxNyJ3wg"
  platform_principal       = "6U66BKFW28"
  apple_platform_team_id   = "6450392486"
  apple_platform_bundle_id = "com.gse.sid"
}